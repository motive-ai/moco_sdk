/** \file spring_example.cpp
 * \brief Demonstrates real-time feedback control.
 *
 * Send a command to the actuator produce a torque opposite the external torque it is experiencing, making
 * it behave like a spring.
 *
 * (c) 2018 Motive Mechatronics, Inc.
 */
#include <iostream>
#include <moco_usb_manager.h>
#include <moco_usb.h>
#include <data_packet_types.h>

using namespace Motive;

int main(int argc, char *argv[]) {
    // MocoUSBManager handles USB device enumeration
    MocoUSBManager manager;
    auto moco_list = manager.connected_boards();
    if (moco_list.empty()) {
        std::cerr << "No Moco found" << std::endl;
        return(1);
    }
    //connect to first moco
    std::shared_ptr<MocoUSB> moco;
    try {
        moco = std::make_shared<MocoUSB>(moco_list[0]);
    } catch (std::exception &e) {
        std::cerr << "Moco not available. Check if another process is already connected." << std::endl;
        return(1);
    }
    if (!moco->is_connected()) {
        std::cerr << "Could not connect to Moco " << moco_list[0] << std::endl;
        return(1);
    }

    std::cout << "Connected to " << moco->get_board_name().name << std::endl;


    // read current actuator state. This is done synchronously as we need to
    // wait on this value before continuing
    auto state = moco->receive(DATA_FMT_ACTUATOR_STATE)->packet().data.status.actuator_state;

    // check if commutation lock is needed
    if ((state.flags >> 16U) & (1U << COMMUTATION_WARNING)) {
        std::cout << "Performing commutation lock..." << std::flush;
        auto phase_lock_mode_param_packet = moco->packet(DATA_FMT_PHASE_LOCK_MODE);
        moco->send(phase_lock_mode_param_packet);
        // wait for commutation lock to complete
        std::this_thread::sleep_for(std::chrono::milliseconds(2500));
        std::cout << "done." << std::endl;
    }

    // use output torque value as a zero point
    auto initial_torque = state.output_torque;
    auto initial_position = state.motor_position;

    // send command to put moco into torque-sensing compensation mode
    auto resp = moco->send("mode", "analog", true);

    // wait for acknowledgement of mode change
    if (resp->wait_for(std::chrono::milliseconds(500)) != std::future_status::ready) {
        std::cerr << "Did not receive confirmation of mode change" << std::endl;
        return(1);
    }

    // send an initial desired torque (which is our current torque)
    auto torque_command = moco->packet(DATA_FMT_ANALOG_COMMAND).packet();
    torque_command.data.command.analog.analog_desired = initial_torque;
    resp = moco->send(torque_command, true);
    if (resp->wait_for(std::chrono::milliseconds(500))  != std::future_status::ready) {
        std::cerr << "Did not receive confirmation of initial torque command" << std::endl;
        return(1);
    }

    float spring_constant = .5;

    /// Create a function to be called each time data is received from the actuator
    /// The code below uses a lambda function, but this can be any function that returns a boolean, and takes
    /// a MocoData pointer. \sa CallbackFunction
    auto callback_fn = [moco, spring_constant, initial_position, initial_torque](auto data) {
        auto current_position = data->packet().data.status.actuator_state.motor_position;
        // send a command that updates the set-point of the torque value based on Hooke's law: F = -k*x
        // Accounting for our initial values, we have F = -(k*(x - x_0) - F_0)
        moco->send("command", "analog", false,
                   {{"analog_desired", -(spring_constant * (current_position - initial_position) - initial_torque)}});
        return true;
    };

    /// Add the callback to the moco, which will get called every time the actuator state data is updated
    moco->add_input_handler(callback_fn, DATA_FMT_ACTUATOR_STATE);

    std::cout << "Turn actuator to feel restorative force. Will exit in 30 seconds." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(30));
    std::cout << "exiting after 30 seconds" << std::endl;
    moco->send("mode", "open", true).get();
    return 0;
}
