/** \file c_api_example.c
 * \brief Demonstrates use of the ZMQ level API of the MoCo controller from Motive Mechatronics.
 *
 * In order for this demo to function, a MoCo should be connected, and `moco_connect` should be running on default ports
 * This will receive several packets from the MoCo, then put it into Phase Lock mode, stay there for three seconds,
 * then put it into Open mode.
 */

#include <stdio.h>
#include <stdlib.h>
#include <data_packet_types.h>
#include <data_packet.h>
#include <zmq_mpd.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
int Sleep(uint32_t sleepMs) { return usleep(sleepMs * 1000); }
#endif

/** Helper function to send a 'mode' packet
 *
 * @param ctx An initialized context
 * @param params Filled in parameters
 * @param mode_id DATA_FMT_*_MODE
 * @return Number of bytes sent, 0 on error
 */
int send_mode_packet(ZmpdCtx *ctx, GenericControllerParams *params, DataFormats mode_id) {
    GenericPacket *packet = CreatePacket();
    GenericData data;
    if (mode_id < DATA_FMT_OPEN_MODE || mode_id > DATA_FMT_NO_MODE) {
        fprintf(stderr, "mode_id not set to a correct default command mode\n");
        return 0;
    }
    data.mode = *params;
    SetData(packet, &data, sizeof(GenericControllerParams), mode_id, 0);
    int bytes_sent = moco_send_packet(ctx, packet);
    free(packet);
    return bytes_sent;
}

/** Helper function to send a 'command' packet
 *
 * @param ctx An initialized context
 * @param command Filled in command parameters
 * @param command_id DATA_FMT_*_COMMAND
 * @return Number of bytes sent, 0 on error
 */
int send_command_packet(ZmpdCtx *ctx, GenericControllerCommands *command, DataFormats command_id) {
    GenericPacket *packet = CreatePacket();
    GenericData data;
    if (command_id < DATA_FMT_OPEN_COMMAND || command_id > DATA_FMT_NO_COMMAND) {
        fprintf(stderr, "Command_id not set to a correct default command command_id\n");
        return 0;
    }
    data.command = *command;
    SetData(packet, &data, sizeof(GenericControllerCommands), command_id, 0);
    int bytes_sent = moco_send_packet(ctx, packet);
    free(packet);
    return bytes_sent;
}


int main(int argc, char *argv[]) {
    // Create an uninitialized context pointer
    ZmpdCtx *ctx = 0;
    // Initialize, setting the send and receive ports, as well as the host. Using '0' for serial ensures we'll talk
    //   to any available board. 6511 is the standard send port, and 6510 is the standard receive port
    moco_zmpd_init(&ctx, 6511, 6510, "localhost", 0);


    // Receive some packets
    int num_packets = 100;
    // allocate memory for 100 packets
    GenericPacket *packet_list = (GenericPacket *) malloc(sizeof(GenericPacket)*num_packets);
    int num_received_packets = 0;
    Sleep(1000); // give some time for packets to arrive
    // actually receive the packets. This will take as many packets as possible from the receive buffer, up to num_packets
    num_received_packets = moco_get_packets(ctx, packet_list, num_packets);
    printf("Received %d packets\n", num_received_packets);
    for (int i=0;i<num_received_packets; i++) {
        printf("Packet %d: was sent at time %u of type %d and data size %d\n", i,
               packet_list[i].header.microseconds, packet_list[i].header.data_format, packet_list[i].header.data_size);
        // Do stuff with the data
    }


    // Another way to receive packets
    GenericPacket *packet = CreatePacket();
    for (int i=0;i<5; i++) {
        int got_packet = moco_get_last_packet(ctx, packet, DATA_FMT_ACTUATOR_STATE);
        if (got_packet) {
            printf("Got 'Actuator State' packet\n");
        }
    }


    //Send a phase lock packet
    int bytes_sent = 0;
    // No matter which mode we'll be entering, we fill in a GenericControllerParams
    GenericControllerParams phase_lock_mode;
    // Set a phase lock current. Check your motor data sheet for appropriate values
    phase_lock_mode.phase_lock.current_param.max_current = 1.0;
    phase_lock_mode.phase_lock.phase_lock_current = 1.0;
    printf("Entering Phase Lock...\n");
    bytes_sent = send_mode_packet(ctx, &phase_lock_mode, DATA_FMT_PHASE_LOCK_MODE);
    printf("Sent %d bytes\n", bytes_sent);

    // Stay in phase lock for 3 seconds...
    Sleep(3000);

    // Now go to Open mode

    // open mode doesn't have any meaningful parameters, so we don't need to populate this
    GenericControllerParams open_mode;
    printf("Entering Open Mode...\n");
    bytes_sent = send_mode_packet(ctx, &open_mode, DATA_FMT_OPEN_MODE);
    printf("Sent %d bytes\n", bytes_sent);


    // We need to give time for command to send before stopping
    Sleep(1000);
    return 0;
}
