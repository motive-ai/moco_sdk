/** \file buffer_example.cpp
 * \brief Demonstrates use of the low level API of the MoCo controller from Motive Mechatronics.
 *
 * For this demo to function, a MoCo should be connected and NEITHER moco_connect or moco_manager should be running
 * This will demonstrate two different methods for asynchronously accessing data. A more complex
 * example of similar buffering is found in /sa position_example.cpp
 *
 * (c) 2018 Motive Mechatronics, Inc.
 */
#include "buffer.h"
#include "moco_usb.h"
#include "moco_usb_manager.h"
#include "data_packet_types.h"
#include <iostream>

using namespace Motive;

// shallow buffer will store the last packet of each type
MocoShallowDataBuffer buffer;

int main(int argc, char *argv[]) {

    // connect to the first Moco found
    auto boards = MocoUSBManager().connected_boards();
    if (boards.empty()) {
        std::cerr << "No connected board" << std::endl;
        exit(1);
    }
    std::cout << "Connecting to " << boards[0] << std::endl;
    MocoUSB actuator(boards[0]);

    // setup a callback function that writes data to the buffer
    auto f = [](std::shared_ptr<const MocoData> d) {
        // the buffer is writen to by a separate thread, so any data access
        // from this function needs to be thread-safe. (MocoShallowDataBuffer is thread-safe)
        // Note that the processing here ties up the main I/O thread, so no complex processing
        //   should take place in this thread.
        buffer.write(d);
        return true;
    };

    // add the callback function to execute whenever data is received from the Moco
    // This is the call that allows the data to be received asynchronously.
    // The function "f" will be called every time new data is available. This functionality should
    // be used to avoid spin-waiting in main loops.
    actuator.add_input_handler(f);

    // make a periodic request packet (by default, actuator state is sent at 1000Hz)
    actuator.send("request", "periodic", true,
                   {{"packet_type", DATA_FMT_ACTUATOR_STATE}, {"rate", 100}}).get();

    // now, with data only coming at 100Hz, the buffer will not always be full when querying every 3ms

    for (auto loop=0; loop < 10; ++loop) {
        // this loop will periodically check if any data is waiting
        for (auto i = 0; i < 10; ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(3));
            // see if there is data waiting
            auto basic = buffer.pop(DATA_FMT_ACTUATOR_STATE);
            if (basic != nullptr) {
                std::cout << basic->as_json() << std::endl;
            } else {
                std::cout << "No data" << std::endl;
            }
        }
        for (auto i = 0; i < 10; ++i) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            int j = 0;
            while (true) {
                auto basic = buffer.pop(DATA_FMT_ACTUATOR_STATE);
                if (basic != nullptr) {
                    std::cout << j++ << " (" << basic->packet().header.microseconds << ") : "
                              << basic->as_json() << std::endl;
                } else {
                    break;
                }
            }
        }
    }
    return 0;
}
