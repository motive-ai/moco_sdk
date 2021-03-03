//THIS FILE IS AUTO-GENERATED. DO NOT EDIT
#define S_FUNCTION_NAME  moco_mode_position
#define S_FUNCTION_LEVEL 2
#define NPARAMS          0

#define IN_PORT_0_NAME moco_ctx
#define IN_PORT_1_NAME kd
#define IN_PORT_2_NAME ki
#define IN_PORT_3_NAME ki_sat
#define IN_PORT_4_NAME kp
#define IN_PORT_5_NAME position_filter_hz
#define IN_PORT_6_NAME velocity_limit
#define IN_PORT_7_NAME velocity_param.kd
#define IN_PORT_8_NAME velocity_param.ki
#define IN_PORT_9_NAME velocity_param.ki_sat
#define IN_PORT_10_NAME velocity_param.kp
#define IN_PORT_11_NAME velocity_param.motor_torque_param.current_param.max_current
#define IN_PORT_12_NAME velocity_param.motor_torque_param.current_param.pi_d.ki
#define IN_PORT_13_NAME velocity_param.motor_torque_param.current_param.pi_d.ki_sat
#define IN_PORT_14_NAME velocity_param.motor_torque_param.current_param.pi_d.kp
#define IN_PORT_15_NAME velocity_param.motor_torque_param.current_param.pi_q.ki
#define IN_PORT_16_NAME velocity_param.motor_torque_param.current_param.pi_q.ki_sat
#define IN_PORT_17_NAME velocity_param.motor_torque_param.current_param.pi_q.kp
#define IN_PORT_18_NAME velocity_param.motor_torque_param.kt
#define IN_PORT_19_NAME velocity_param.velocity_filter_hz

#include "simstruc.h"
#include "moco_mode_position.h"

static void mdlInitializeSizes(SimStruct *S) {
    int_T nInputPorts  = 20;  // number of input ports
    int_T nOutputPorts = 0;  // number of output ports
    int_T needsInput   = 1;  // direct feed through

    int_T inputPortIdx  = 0;
    int_T outputPortIdx = 0;

    ssSetNumSFcnParams(S, NPARAMS);  // Number of expected parameters
    if (ssGetNumSFcnParams(S) != ssGetSFcnParamsCount(S)) {
        return;
    }

    // Register the number and type of states the S-Function uses
    ssSetNumContStates(    S, 0);   // number of continuous states
    ssSetNumDiscStates(    S, 0);   // number of discrete states

    
#ifdef MATLAB_MEX_FILE
    mxArray *normInputs[3];
    mxArray *normOutputs[1];
    //first check if we are linked to a library
//see: https://www.mathworks.com/help/simulink/ug/control-linked-block-status-programmatically.html
    normInputs[0] = mxCreateString(ssGetPath(S));
    normInputs[1] = mxCreateString("StaticLinkStatus");
    mexCallMATLAB(1, normOutputs, 2, normInputs, "get_param");
    const int *dim_array = mxGetDimensions(normOutputs[0]);
    printf("Dim: %d %d\n", dim_array[0], dim_array[1]);
    if (dim_array[1] < 5) { //not linked
        normInputs[1] = mxCreateString("Mask");
        normInputs[2] = mxCreateString("on");
        mexCallMATLAB(0, 0, 3, normInputs, "set_param");
        mxDestroyArray(normInputs[1]);
        normInputs[1] = mxCreateString("MaskDisplay");
        mxDestroyArray(normInputs[2]);
        normInputs[2] = mxCreateString("port_label('input', 1, 'moco_ctx');port_label('input', 2, 'kd');port_label('input', 3, 'ki');port_label('input', 4, 'ki_sat');port_label('input', 5, 'kp');port_label('input', 6, 'position_filter_hz');port_label('input', 7, 'velocity_limit');port_label('input', 8, 'velocity_param.kd');port_label('input', 9, 'velocity_param.ki');port_label('input', 10, 'velocity_param.ki_sat');port_label('input', 11, 'velocity_param.kp');port_label('input', 12, 'velocity_param.motor_torque_param.current_param.max_current');port_label('input', 13, 'velocity_param.motor_torque_param.current_param.pi_d.ki');port_label('input', 14, 'velocity_param.motor_torque_param.current_param.pi_d.ki_sat');port_label('input', 15, 'velocity_param.motor_torque_param.current_param.pi_d.kp');port_label('input', 16, 'velocity_param.motor_torque_param.current_param.pi_q.ki');port_label('input', 17, 'velocity_param.motor_torque_param.current_param.pi_q.ki_sat');port_label('input', 18, 'velocity_param.motor_torque_param.current_param.pi_q.kp');port_label('input', 19, 'velocity_param.motor_torque_param.kt');port_label('input', 20, 'velocity_param.velocity_filter_hz');disp('moco_mode_position')");
        mexCallMATLAB(0, 0, 3, normInputs, "set_param");
        mxDestroyArray(normInputs[0]);
        mxDestroyArray(normInputs[1]);
        mxDestroyArray(normInputs[2]);
    }
#endif

    // Configure the input ports. First set the number of input ports.
    if (!ssSetNumInputPorts(S, nInputPorts)) return;
    if (nInputPorts > 0) {
        ssSetInputPortWidth(S, 0, 1);
        ssSetInputPortDataType(S, 0, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 0, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 0, 1);
        ssSetInputPortWidth(S, 1, 1);
        ssSetInputPortDataType(S, 1, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 1, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 1, 1);
        ssSetInputPortWidth(S, 2, 1);
        ssSetInputPortDataType(S, 2, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 2, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 2, 1);
        ssSetInputPortWidth(S, 3, 1);
        ssSetInputPortDataType(S, 3, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 3, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 3, 1);
        ssSetInputPortWidth(S, 4, 1);
        ssSetInputPortDataType(S, 4, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 4, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 4, 1);
        ssSetInputPortWidth(S, 5, 1);
        ssSetInputPortDataType(S, 5, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 5, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 5, 1);
        ssSetInputPortWidth(S, 6, 1);
        ssSetInputPortDataType(S, 6, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 6, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 6, 1);
        ssSetInputPortWidth(S, 7, 1);
        ssSetInputPortDataType(S, 7, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 7, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 7, 1);
        ssSetInputPortWidth(S, 8, 1);
        ssSetInputPortDataType(S, 8, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 8, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 8, 1);
        ssSetInputPortWidth(S, 9, 1);
        ssSetInputPortDataType(S, 9, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 9, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 9, 1);
        ssSetInputPortWidth(S, 10, 1);
        ssSetInputPortDataType(S, 10, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 10, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 10, 1);
        ssSetInputPortWidth(S, 11, 1);
        ssSetInputPortDataType(S, 11, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 11, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 11, 1);
        ssSetInputPortWidth(S, 12, 1);
        ssSetInputPortDataType(S, 12, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 12, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 12, 1);
        ssSetInputPortWidth(S, 13, 1);
        ssSetInputPortDataType(S, 13, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 13, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 13, 1);
        ssSetInputPortWidth(S, 14, 1);
        ssSetInputPortDataType(S, 14, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 14, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 14, 1);
        ssSetInputPortWidth(S, 15, 1);
        ssSetInputPortDataType(S, 15, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 15, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 15, 1);
        ssSetInputPortWidth(S, 16, 1);
        ssSetInputPortDataType(S, 16, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 16, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 16, 1);
        ssSetInputPortWidth(S, 17, 1);
        ssSetInputPortDataType(S, 17, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 17, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 17, 1);
        ssSetInputPortWidth(S, 18, 1);
        ssSetInputPortDataType(S, 18, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 18, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 18, 1);
        ssSetInputPortWidth(S, 19, 1);
        ssSetInputPortDataType(S, 19, SS_DOUBLE);
        ssSetInputPortComplexSignal(S, 19, COMPLEX_NO);
        ssSetInputPortDirectFeedThrough(S, 19, 1);

        //if(!ssSetInputPortDimensionInfo(S, inputPortIdx, DYNAMIC_DIMENSION)) return;

        // A port has direct feedthrough if the input is used in either the mdlOutputs
        //   or mdlGetTimeOfNextVarHit functions.
    }
    // Configure the output ports. First set the number of output ports.
    if (!ssSetNumOutputPorts(S, nOutputPorts)) return;
    if (nOutputPorts > 0) {
        

        // Set output port dimensions for each output port index starting at 0.
        //if(!ssSetOutputPortDimensionInfo(S,outputPortIdx,DYNAMIC_DIMENSION)) return;
    }

    ssSetNumSampleTimes(   S, 1);   // number of sample times

    // Set size of the work vectors.
    ssSetNumRWork(         S, 0);   // number of real work vector elements
    ssSetNumIWork(         S, 0);   // number of integer work vector elements
    ssSetNumPWork(         S, 1);   // number of pointer work vector elements
    ssSetNumModes(         S, 0);   // number of mode work vector elements
    ssSetNumNonsampledZCs( S, 0);   // number of nonsampled zero crossings

    // Specify the sim state compliance to be same as a built-in block
    ssSetSimStateCompliance(S, USE_DEFAULT_SIM_STATE);

    ssSetOptions(          S, 0);   // general options

} // end mdlInitializeSizes


static void mdlInitializeSampleTimes(SimStruct *S) {
    // Register one pair for each sample time
    ssSetSampleTime(S, 0, INHERITED_SAMPLE_TIME);
    ssSetOffsetTime(S, 0, 0.0);
}

#define MDL_INITIALIZE_CONDITIONS
#if defined(MDL_INITIALIZE_CONDITIONS)
static void mdlInitializeConditions(SimStruct *S) {}
#endif


#define MDL_START
#if defined(MDL_START)
static void mdlStart(SimStruct *S) {
    
}
#endif


static void mdlOutputs(SimStruct *S, int_T tid) {
    moco_mode_position_outputs(S);
}


#define MDL_UPDATE
#if defined(MDL_UPDATE)
static void mdlUpdate(SimStruct *S, int_T tid) {
    
}
#endif


#define MDL_DERIVATIVES
#if defined(MDL_DERIVATIVES)
static void mdlDerivatives(SimStruct *S) {

}
#endif


static void mdlTerminate(SimStruct *S) {
    
}


//*=============================*
//* Required S-function trailer *
//*=============================*

#ifdef  MATLAB_MEX_FILE    // Is this file being compiled as a MEX-file?
#include "simulink.c"      // MEX-file interface mechanism
#else
#include "cg_sfun.h"       // Code generation registration function
#endif
