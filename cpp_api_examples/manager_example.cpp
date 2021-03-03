/** \file manager_example.cpp
 * \brief Demonstrates use of the Manager Interface of the MoCo controller from Motive Mechatronics.
 *
 * In order for this demo to function, a MoCo should be connected, and `moco_manager` should be running.
 * This will receive several packets from the MoCo, then put it into Phase Lock mode, stay there for one second,
 * then put it into Open mode.
 *
 * (c) 2018 Motive Mechatronics, Inc.
 */

#include <iostream>
#include <moco_manager.h>

using namespace Motive;


int no_error_checking() {
    MocoManager manager("tcp://localhost:6500");
    auto moco_ids = manager.list_mocos();
    auto actuator = manager.get_moco(moco_ids[0]);
    auto res = actuator->send("mode", "phase_lock", true, R"({ "phase_lock_current": 1.5 })"_json);
    std::cout << "Sent: " << res->get()->as_json(true).dump(2) << std::endl;
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    res = actuator->send(DATA_FMT_OPEN_MODE, true);
    std::cout << "Sent: " << res->get()->as_json(true) << std::endl;
    return 0;
}

int with_error_checking() {
    MocoManager manager;
    try {
        manager = MocoManager("tcp://localhost:6500");
    } catch (std::exception &e) {
        std::cerr << "Could not retrieve configuration: " << e.what() << std::endl;
        exit(1);
    }

    auto moco_ids = manager.list_mocos();
    if (moco_ids.empty()) {
        std::cerr << "No Mocos found in config." << std::endl;
        exit(1);
    }
    auto actuator = manager.get_moco(moco_ids[0]);
    if (not actuator->is_connected()) {
        std::cerr << "Could not connect to " << actuator->get_serial() << std::endl;
        exit(1);
    }
    std::unique_ptr<MocoDataFuture> res;
    try {
        res = actuator->send("mode", "phase_lock", true, R"({ "phase_lock_current": 1.5 })"_json);
    } catch (std::out_of_range &e) {
        fprintf(stderr, "Could not send packet. Unknown type\n");
    } catch (nlohmann::json::exception &e) {
        fprintf(stderr, "Could not send packet. %s\n", e.what());
    }
    if (res->wait_for(std::chrono::milliseconds(2000)) == std::future_status::ready) {
        std::cout << "Sent: " << res->get()->as_json(true).dump(2) << std::endl;
    } else {
        std::cerr << "Did not confirm receipt of phase lock" << std::endl;
    }
    // wait one second...
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    // return to open mode
    res = actuator->send(DATA_FMT_OPEN_MODE, true);
    if (res->wait_for(std::chrono::milliseconds(2000)) == std::future_status::ready) {
        std::cout << "Sent: " << res->get()->as_json(true) << std::endl;
    } else {
        std::cerr << "Did not confirm receipt of open mode" << std::endl;
    }
    return 0;
}


int main(int argc, char *argv[]) {
    with_error_checking();
}