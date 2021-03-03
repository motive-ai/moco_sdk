/*
 * (c) 2018 Motive Mechatronics, Inc.
 */
#include <moco_usb_manager.h>
#include <moco_usb.h>
#include <moco_zmq.h>
#include <data_packet_types.h>
#include <iostream>

using namespace Motive;

/* Demonstrate receiving data, and sending a packet and receiving an acknowledgement.
 * This example connects via moco_connect, which must already be running */

int main(int argc, char *argv[]) {
    auto serials = MocoUSBManager().connected_boards();
    if (serials.empty()) {
        std::cerr << "No connected boards." << std::endl;
        exit(1);
    }

    // choose connection method:

    //MocoZMQ actuator(serials[0], "tcp://localhost:6511", "tcp://localhost:6510");
    MocoUSB actuator(serials[0]);


    if (!actuator.is_connected()) {
        std::cerr << "Not connected! Run moco_connect and try again." << std::endl;
        exit(1);
    }

    // perform a synchronous receive and display the data
    // For an example of asynchronous data receive, see `buffer_example`
    auto data = actuator.receive(DATA_FMT_ACTUATOR_STATE);
    if (data != nullptr) {
        auto data_string = data->as_json().dump(2);
        std::cout << "Received data: " << data_string << std::endl;
    } else {
        std::cerr << "No data received!" << std::endl;
    }

    // send a phase lock packet
    auto outgoing_packet = actuator.packet(DATA_FMT_PHASE_LOCK_MODE).packet();
    outgoing_packet.data.mode.phase_lock.current_param.max_current = 1.0;
    outgoing_packet.data.mode.phase_lock.phase_lock_current = 1.0;
    auto status = std::future_status::timeout;
    std::shared_ptr<const MocoData> response;
    while (status != std::future_status::ready) {
        std::cout << "Sending phase-lock" << std::endl;
        auto future = actuator.send(outgoing_packet, true);
        status = future->wait_for(std::chrono::milliseconds(1000));
        response = future->get();
    }
    std::cout << "Received back: " << response->as_json() << std::endl;
    //wait for two seconds
    std::this_thread::sleep_for(std::chrono::milliseconds(2000));

    printf("Sending Open mode\n");
    try {
        auto future = actuator.send("mode", "open", true);
        future->wait();
        std::cout << "Received back: " << future->get()->hex() << std::endl;
    } catch (std::out_of_range &e) {
        fprintf(stderr, "Could not send packet. Unknown type\n");
    } catch (nlohmann::json::exception &e) {
        fprintf(stderr, "Could not send packet. %s\n", e.what());
    }

    printf("Done.\n");
    return 0;
}