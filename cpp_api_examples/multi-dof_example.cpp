/** \file multi-dof_example.cpp
 * \brief Demonstrates the Chain and RobotState API for kinematic chain control.
 *
 * In order for this demo to function, a MoCo should be connected,
 * optionally `moco_manager` should be running on default ports.
 * This example will connect to all given joints (see 'joint_names'), and command them
 * in position mode for 5 seconds to perform a sine wave of amplitude .2 radians
 *
 * (c) 2018 Motive Mechatronics, Inc.
 */
#include <iostream>
#include <moco_manager.h>
#include <data_packet_types.h>
#include <chain.h>
#include <nlohmann/json.hpp>
#include <moco_usb_manager.h>

using namespace Motive;

// Requires 'moco_manager' to be running, which sets up tcp IPC to send and receive data
std::shared_ptr<Chain> get_chain_through_manager(std::string chain_name, std::vector<std::string> joint_names) {
    MocoManager manager;
    const std::string manager_connection = "tcp://localhost:6500";
    try {
        manager = MocoManager(manager_connection);
    } catch (...) {
        std::cerr << "could not connect to manager on: " << manager_connection << std::endl;
        exit(1);
    }

    // Retrieve a chain. This will start data collection in the background at default rate (1000 Hz)
    auto chain = manager.get_chain(chain_name, joint_names);
    return chain;
}

std::shared_ptr<Chain> get_chain_by_usb(std::string chain_name, std::vector<std::string> joint_names) {
    // create a chain using to specified joint ordering
    // note that the chain may not contain all specified joints if they cannot be connected to over USB
    auto chain = std::make_shared<Chain>(chain_name, joint_names);
    if (chain->size() != joint_names.size()) {
        std::cerr << "Could not connect to all requested joints" << std::endl;
    }
    return chain;
}

int main(int argc, char *argv[]) {
    // The name of the kinematic chain, as configured on the Mocos. Use 'moco_connect -l' to list
    std::string chain_name = "MCA";

    // Ordered list of joints to connect. Should match URDF joint names, and be configured on Mocos
    std::vector<std::string> joint_names = {"T1", "T2", "J3"};

    MocoUSBManager manager;
    auto moco_list = manager.connected_boards();
    // Choose which way you want to connect: Direct USB or using IPC
    auto chain = std::make_shared<Chain>(moco_list);
    //auto chain = get_chain_by_usb(chain_name, joint_names);
    //auto chain = get_chain_through_manager(chain_name, joint_names);

    // Change the RobotState update rate (optional)
    chain->set_update_rate(100); // [Hz], range 1~5000

    // error checking
    if (chain->size() == 0) {
        std::cerr << "Did not connect to any joints" << std::endl;
        exit(1);
    }
    // more error checking
    for (int i = 0; i < chain->size(); ++i) {
        // send an active, synchronous ping to the actuator
        if (!chain->get_moco_by_index(i)->is_connected()) {
            std::cerr << "Did not get response from actuator " << i << std::endl;
        }
    }

    // Get the current state of the robot. This call does not block. It will always return the latest data.
    RobotState state = chain->get_state();

    // print all the data using json...
    std::cout << nlohmann::json(state) << std::endl;

    // ... or just some of it
    auto start_positions = state.joint_position;
    std::cout << "Starting positions are: " << std::endl;
    for (int i = 0; i < start_positions.size(); ++i) {
        // lookup data about the joint
        auto name = chain->get_moco_by_index(i)->get_board_name().name;
        std::cout << name << ": " << start_positions[i] << std::endl;
    }

    // Create vector of Position-mode commands to send
    std::vector<std::shared_ptr<ActuatorCommand>> cmds;
    for (auto pos : start_positions) {
        auto a = std::make_shared<ActuatorPositionCommand>();
        // set to current robot position
        a->set_position_command(pos, 0, 0);
        cmds.emplace_back(a);
    }

    // you can address an individual actuator
    auto j1 = chain->get_moco_by_index(0); // Zero-based

    // anything you can do with a single actuator, you can do here
    auto data = j1->request(DATA_FMT_MOTOR_DETAIL); // synchronous call
    if (data) {
        auto motor_detail_json = data->as_json();
        std::cout << "Motor data for first joint: " << motor_detail_json.dump(2);
    }

    // initialize the actuators, if needed
    int i = 0;
    bool lock_needed = false;
    for (const auto &moco : chain->get_mocos()) {
        moco->send("request", "clear_flags", true)->wait_for(std::chrono::milliseconds(10));
        if ((state.fault_flags[i] >> 16U) & (1U << COMMUTATION_WARNING)) {
            lock_needed = true;
            std::cout << "Performing commutation lock on " << moco->get_board_name().name << "..." << std::endl;
            auto phase_lock_mode_param_packet = moco->packet(DATA_FMT_PHASE_LOCK_MODE);
            moco->send(phase_lock_mode_param_packet);
        }
        ++i;
    }
    if (lock_needed) {
        // wait for commutation lock to complete
        std::this_thread::sleep_for(std::chrono::milliseconds(2500));
        std::cout << "done." << std::endl;
    }

    // send one-off command to go to current position
    // if any actuator isn't in position mode, this will put it in position mode
    //  using default parameters
    try {
        chain->send_command(cmds);
    } catch (std::exception &e) {
        std::cerr << "Could not set joint to position mode. Check for an error flag, and retry." << std::endl;
        return(1);
    }
    // There is no time requirement, so you can do other things on this thread, ie:
    std::this_thread::sleep_for(std::chrono::milliseconds(100)); // dummy sleep


    // == Execute a sin function for 5 seconds ==

    const std::chrono::milliseconds dt(10); // You can update at any rate you want, up to ~5KHz
    std::chrono::time_point<hrclock> start_time = hrclock::now();
    auto end_time = start_time + std::chrono::seconds(5);
    auto curr_time = start_time;

    double amplitude = .5; // [radians]
    double freq = .5; // [Hz]
    while (curr_time < end_time) {
        double elapsed_secs = std::chrono::duration_cast<std::chrono::microseconds>
                (hrclock::now() - start_time).count() / 1e6;
        double pos_desired = amplitude * sin(2 * M_PI * freq * elapsed_secs);
        auto curr_state = chain->get_state();
        for (int i = 0; i < cmds.size(); ++i) {
            double desired_pos = start_positions[i] + pos_desired;
            std::cout << elapsed_secs << ": desired: " << desired_pos <<
                         " actual: " << curr_state.joint_position[i] << std::endl;
            auto cmd = dynamic_cast<ActuatorPositionCommand*>(cmds[i].get());
            cmd->set_position_command(static_cast<float>(desired_pos), 2*amplitude/freq, 0);
            // could also use:
            // cmds[i]->update(start_positions[i] + f);
            // which works in impedance or position mode
            // OR
            // using low-level commands, one joint at a time (not recommended if using chains):
            // chain->get_moco_by_index(i)->send_command(*cmd);
        }
        // open-loop control. Does not wait / check for actuator to arrive at position
        chain->send_command(cmds); // send update to all actuators
        curr_time += dt;
        std::this_thread::sleep_until(curr_time);
    }

    // create open mode commands
    for (auto i = 0; i < cmds.size(); i++) {
        cmds[i] = std::make_shared<ActuatorOpenCommand>();
    }

    // set to open mode
    chain->send_command(cmds);

    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    return 0;
}
