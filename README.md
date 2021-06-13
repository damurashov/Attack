# On the project, briefly

## Concept

Locks a copter view direction on a target using the copter's camera as a sensor. The control loop is essentially the
simplest PID controller (the implementation is courtesy of https://pypi.org/project/simple-pid/).

A client sends regular stick control information, as if the copter was operated manually. The communication chain looks as
follows:

```
copter(camera) --> wifi(image)       --> client
client         --> wifi(RC channels) --> copter
```

## Main components

- `controller` - PID controller implementation
- `tracker_propagation` - tracker implementation
- `ui_control` - Manual control, the working example demostrating capabilities of the system

## `ui_control`, manual

Method `__instantiate_key_mappings` of `ui_control.UiControl` is pretty much self exaplainatory. Use it
as your starting point.

Modes get switched by `0`, `1`, or `2` keyboard keys. The following mapping is used (as for 2021-06-13, `Pioneer Mini`
standard parameters):

- `0` - stabilize (hold horizontal orientation)
- `1` - althold (`stabilize` + hold altitude)
- `2` - navigation (`althold` + hold position)

## Tools

The project's components write logs while operating. Log is a csv file. As for 2021-06-13, the `ui_control`
module produces 3 types of logs

- `log-engage-*` -- log containing information on control action inferred from `x` and `y` errors which are essentially
offsets between center of a camera frame and a traced object boundary's center. The log is written for as long as a
control action is being imposed on the vehicle.
- `log-events-*` -- system events of different kind
- `log-rc-*` -- information on RC channels sent to the vehicle.

You can plot `log-rc` and `log-engage` as a covenient graph. Call `make plot_rc` or `make plot_engage` respectively.