#!/usr/bin/python3

import threading

from PID import PID
from args import getarparser
from controller import AttackStrategyPixels, AttackStrategy, AttackStrategyAngles


class ParametersPidAngles:
    P_VERTICAL_PID = 0.0
    I_VERTICAL_PID = 0.0
    D_VERTICAL_PID = 0.0

    P_HORIZONTAL_PID = 0.0
    I_HORIZONTAL_PID = 0.0
    D_HORIZONTAL_PID = 0.0

    DELTA_ENGAGE_THRESHOLD_PRELIMINARY = 0.0
    DELTA_ENGAGE_THRESHOLD_CLEAN = 0.0

    CONTROL_VERTICAL_RANGE = (-0.7, 0.7,)
    CONTROL_HORIZONTAL_RANGE = (-1.0, 1.0)

    N_ITERATIONS_CONTROL_LAG = 0


class ParametersPidPixels:
    P_VERTICAL_PID = 0.3
    I_VERTICAL_PID = 0.08
    D_VERTICAL_PID = 0.0

    P_HORIZONTAL_PID = 0.7
    I_HORIZONTAL_PID = 0.06
    D_HORIZONTAL_PID = 0.0

    DELTA_ENGAGE_THRESHOLD_PRELIMINARY = 0.04
    DELTA_ENGAGE_THRESHOLD_CLEAN = 0.02

    CONTROL_VERTICAL_RANGE = (-0.2, 0.2,)
    CONTROL_HORIZONTAL_RANGE = (-0.2, 0.2,)

    # Number of iterations the controller will wait skip before it starts imposing a control action
    N_ITERATIONS_CONTROL_LAG = 3

SETPOINT = 0  # The deviation should be "0"
SAMPLE_TIME = None  # "dt" gets updated manually


class Control:
    def __init__(self):
        self.controller: AttackStrategy = Control.__instantiate_controller()
        self.thread_rc_pid = Control.__instantiate_thread_rc(self.controller)

    @staticmethod
    def __instantiate_thread_rc(controller: AttackStrategy):
        thread_rc_pid = threading.Thread(target=controller.push_rc_task)
        thread_rc_pid.start()
        return thread_rc_pid

    @staticmethod
    def __instantiate_controller():
        pid_input = getarparser().parse_args().pid_input

        pid_to_class_mapping = {
            'pixels': (ParametersPidPixels, AttackStrategyPixels),
            'angles': (ParametersPidAngles, AttackStrategyAngles),
        }

        ParametersClass, StrategyClass = pid_to_class_mapping[pid_input]

        pid_vertical = PID(ParametersClass.P_VERTICAL_PID,
                           ParametersClass.I_VERTICAL_PID,
                           ParametersClass.D_VERTICAL_PID,
                           SETPOINT,
                           SAMPLE_TIME)

        pid_horizontal = PID(ParametersClass.P_HORIZONTAL_PID,
                             ParametersClass.I_HORIZONTAL_PID,
                             ParametersClass.D_HORIZONTAL_PID,
                             SETPOINT,
                             SAMPLE_TIME)

        delta_threshold_preliminary = ParametersClass.DELTA_ENGAGE_THRESHOLD_PRELIMINARY
        delta_threshold_clean = ParametersClass.DELTA_ENGAGE_THRESHOLD_CLEAN
        n_iterations_control_lag = ParametersClass.N_ITERATIONS_CONTROL_LAG

        control_horizontal_range = ParametersClass.CONTROL_HORIZONTAL_RANGE
        control_vertical_range = ParametersClass.CONTROL_VERTICAL_RANGE

        return StrategyClass(pid_vertical=pid_vertical,
                             pid_horizontal=pid_horizontal,
                             delta_threshold_preliminary=delta_threshold_preliminary,
                             delta_threshold_clean=delta_threshold_clean,
                             n_iterations_control_lag=n_iterations_control_lag,
                             control_horizontal_range=control_horizontal_range,
                             control_vertical_range=control_vertical_range)
