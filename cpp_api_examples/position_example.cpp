/** \file position_example.cpp
 * \brief Demonstrates position control of an actuator.
 *
 * In order for this demo to function, a MoCo should be connected, and `moco_manager` should be running on default ports
 * This will receive several packets from the MoCo, then put it into Position mode, command it to a desired_pos,
 * then put it into Open mode.
 *
 * (c) 2018 Motive Mechatronics, Inc.
 */

#define _USE_MATH_DEFINES
#include <iostream>
#include <moco_manager.h>
#include <data_packet_types.h>
#include <moco_usb_manager.h>
#include <moco_usb.h>

using namespace Motive;
using hrclock = std::chrono::high_resolution_clock;

MocoShallowDataBuffer buffer;

/* This example uses MocoManager to retrieve configuration data for the board
 * In order to use this example, you should have moco_manager running
 */


int main(int argc, char *argv[]) {
    // MocoUSBManager handles USB device enumeration
    MocoUSBManager manager;
    auto moco_list = manager.connected_boards();
    if (moco_list.empty()) {
        std::cerr << "No Moco found" << std::endl;
        exit(1);
    }
    //connect to first moco from manager
    auto moco = std::make_shared<MocoUSB>(moco_list[0]);
    if (!moco->is_connected()) {
        std::cerr << "Could not connect to Moco " << moco_list[0] << std::endl;
        exit(1);
    }

    std::cout << "Connected to " << moco->get_board_name().name << std::endl;

    // request ACTUATOR_STATE data at 2000Hz
    auto resp = moco->send("request", "periodic", true,
            {{"packet_type", DATA_FMT_ACTUATOR_STATE}, {"rate", 2000}})->get();
    auto f = [](const std::shared_ptr<const MocoData> &d) {
        buffer.write(d);
        return true;};
    moco->add_input_handler(f);

    auto actuator_state = buffer.pop(DATA_FMT_ACTUATOR_STATE);
    while (actuator_state == nullptr) {
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
        actuator_state = buffer.pop(DATA_FMT_ACTUATOR_STATE);
    }
    if ((actuator_state->generic_data().status.actuator_state.flags >> 16U) & (1U << COMMUTATION_WARNING)) {
        auto phase_lock_mode_param_packet = moco->packet(DATA_FMT_PHASE_LOCK_MODE);
        moco->send(phase_lock_mode_param_packet);
        std::this_thread::sleep_for(std::chrono::milliseconds(3500));
    }
    // set control mode. Uses default mode params
    moco->set_control_mode(Control::Position);
    ActuatorPositionCommand cmd;
    //setup command to move 1 radian from current position
    auto desired_pos = actuator_state->generic_data().status.actuator_state.motor_position + 1;
    cmd.set_position_command(desired_pos, .1);
    //actually command the joint to go to position
    moco->send_command(cmd);

    //setup a simple, fixed frequency loop to check position every 1 ms
    const std::chrono::milliseconds dt(1);
    std::chrono::time_point<hrclock> start_time = hrclock::now();
    auto end_time = start_time + std::chrono::seconds(10);
    auto curr_time = start_time;

    while (curr_time < end_time) {
        // get the most recent data
        auto data = buffer.pop(DATA_FMT_ACTUATOR_STATE);
        if (data) {
            auto pos = data->generic_data().status.actuator_state.motor_position;
            if (fabs(pos - desired_pos) < 1e-2) {
                std::cout << "Arrived at desired position: " << pos*180/M_PI << std::endl;
                break;
            }
        }
        curr_time += dt;
        std::this_thread::sleep_until(curr_time);
    }
    std::cout << "Setting Open mode..." << std::endl;
    moco->send("mode", "open", true);
    std::cout << "Exiting" << std::endl;
    return 0;
}
