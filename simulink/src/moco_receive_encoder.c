//THIS FILE IS AUTO-GENERATED. DO NOT EDIT
#define S_FUNCTION_NAME  moco_receive_encoder
#define S_FUNCTION_LEVEL 2
#define NPARAMS          0

#define OUT_PORT_0_NAME cog
#define OUT_PORT_1_NAME elec_angle
#define OUT_PORT_2_NAME encoder_error
#define OUT_PORT_3_NAME index_count
#define OUT_PORT_4_NAME index_position
#define OUT_PORT_5_NAME mech_angle
#define OUT_PORT_6_NAME raw_position
#define IN_PORT_0_NAME moco_ctx

#include "simstruc.h"
#include "moco_receive_encoder.h"

static void mdlInitializeSizes(SimStruct *S) {
    int_T nInputPorts  = 1;  // number of input ports
    int_T nOutputPorts = 7;  // number of output ports
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
        normInputs[2] = mxCreateString("port_label('output', 1, 'cog');port_label('output', 2, 'elec_angle');port_label('output', 3, 'encoder_error');port_label('output', 4, 'index_count');port_label('output', 5, 'index_position');port_label('output', 6, 'mech_angle');port_label('output', 7, 'raw_position');port_label('input', 1, 'moco_ctx');disp('moco_receive_encoder')");
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

        //if(!ssSetInputPortDimensionInfo(S, inputPortIdx, DYNAMIC_DIMENSION)) return;

        // A port has direct feedthrough if the input is used in either the mdlOutputs
        //   or mdlGetTimeOfNextVarHit functions.
    }
    // Configure the output ports. First set the number of output ports.
    if (!ssSetNumOutputPorts(S, nOutputPorts)) return;
    if (nOutputPorts > 0) {
        ssSetOutputPortWidth(S, 0, 1);
        ssSetOutputPortDataType(S, 0, SS_DOUBLE);
        ssSetOutputPortComplexSignal(S, 0, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 1, 1);
        ssSetOutputPortDataType(S, 1, SS_INT32);
        ssSetOutputPortComplexSignal(S, 1, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 2, 1);
        ssSetOutputPortDataType(S, 2, SS_INT32);
        ssSetOutputPortComplexSignal(S, 2, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 3, 1);
        ssSetOutputPortDataType(S, 3, SS_INT32);
        ssSetOutputPortComplexSignal(S, 3, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 4, 1);
        ssSetOutputPortDataType(S, 4, SS_INT32);
        ssSetOutputPortComplexSignal(S, 4, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 5, 1);
        ssSetOutputPortDataType(S, 5, SS_INT32);
        ssSetOutputPortComplexSignal(S, 5, COMPLEX_NO);
        
        ssSetOutputPortWidth(S, 6, 1);
        ssSetOutputPortDataType(S, 6, SS_INT32);
        ssSetOutputPortComplexSignal(S, 6, COMPLEX_NO);
        

        // Set output port dimensions for each output port index starting at 0.
        //if(!ssSetOutputPortDimensionInfo(S,outputPortIdx,DYNAMIC_DIMENSION)) return;
    }

    ssSetNumSampleTimes(   S, 1);   // number of sample times

    // Set size of the work vectors.
    ssSetNumRWork(         S, 1);   // number of real work vector elements
    ssSetNumIWork(         S, 6);   // number of integer work vector elements
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
    moco_receive_encoder_outputs(S);
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