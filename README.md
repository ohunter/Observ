![The logo](https://github.com/ohunter/Observ/blob/master/observ_logo.png)

A simple curses based system monitor similar to that of glances and htop

## Sample

![A simple example](https://github.com/ohunter/Observ/blob/master/Example.gif)

**NB:** *Please excuse the seemingly poor performance in the example above. My laptop wasn't too happy with recording it. Unless you set the frequency of a module to be absurd the system impact should be marginal.*

## Requirements

- [Blessed](https://github.com/jquast/blessed)
- [Debugpy](https://github.com/microsoft/debugpy) *(Only needed if you plan on running with the `--debug` flag)*

## Arguments

- `-c`: Specifies the location of the configuration file. It is optional as there is a default location.
- `-l`: Specifies the location of the log produced by the process. It is optional, but if the argument is present and there is no secondary argument the location is assumed.
- `-ll`: Specifies the level of logging desired. It maps to 1 to 10 for the logging levels in python.
- `--debug`: Opens a port for debugging purposes. If no secondary value is given the default port is `42069`.

## Configuration

The configuration file is set up to be as extensible as possible. As such it can seem a little daunting at first glance. It consists of a singular Json file which is quite simple. The root object of the file contains a field with the value `screen` which can map to two different things. Either a `tile` object or a `partitions` object.

### `Partitions`

The `partitions` object is the more complex object of the two. It states in what way the area it controls should be divided for the subsequent objects. Theoretically there is no limit to how nested partitions can be other than your own sanity. However; practically it makes sense to stop at a point where you know that the information can be read and displayed clearly. The `partitions` object has two different fields which are obligatory and two which are optional.

#### Partition Fields

| Field Name | Required? | Default | Options |
|---|---|---|---|
|`type`|True|`"tiled"`|`"tiled"` or `"tabbed"`|
|`screens`|True|`N/A`|`N/A`|
|`orientation`|False|`"vertical"`|`"vertical"` or `"horizontal"`|
|`splits`|False|`[]`|`[]` or `[]` filled with `n-1` values|

##### `type`

Describes how the partitions are going to be displayed. It has two accepted values, `"tiled"` and `"tabbed"`. If `"tiled"` then the program will split the area between all the different tiles it is in control over. If `"tabbed"` the area will only display one screen, but it allow for navigation between the different tiles altogether.

##### `screens`

This field is an array of the different objects the partitioning will be in control over. Each object here can be it's own `tile` object or another partition.

##### `orientation`

This field describes how the `"tiled"` partitions will organize themselves. If set to `"vertical"` the tiles will divide themselves across the given space in a vertical manner. If set to `"horizontal"` the tiles will arrange themselves based on the horizontal space available. The default value is `"vertical"`.

##### `splits`

This array describes at what percentage of the area the borders between the different tiles will appear. Only useful for partitions with type `"tiled"`. There are two different possible values for this field. If the field is empty then the partition will divide the space evenly between the different screens. If the field contains any values, it has to contain `n-1` different values otherwise the configuration is invalid. These values should be in increasing order and can be interpreted as a percentage of the area provided to the screen object.

### `Tile`

The `tile` object is the simplest of the objects as it contains a singular module which performs a singular task. There are a variety of different types of tile objects. Some are static and don't do anything; Others update periodically. Depending on the type of `tile` there are different fields to consider. The type of tile id determined by the field `module`.

#### General tile Fields

| Field Name | Optional | Default | Options |
|---|---|---|---|
| `module` | False | `N/A` | See below |
| `border` | True | False | True, False, or an array of all the different characters in the border |
| `title` | True | `""` | Any string |
| `frequency` | True | 1 | Any integer |
| `executed` | True | `"native"` | `"native"`, `"thread"`, or `"process"` |

##### `module`

Describes the general purpose of the object.

##### `border`

Describes how the area shall be decorated if anything.

##### `title`

Describes a string which will be placed at the top of the area.


##### `frequency`

How often the area will be updated.

##### `executed`

This describes how the module will be evaluated. If `"native"` the function will be executed every time the tile is updated. If `"thread"` the function will run in a separate thread controlled by the process and as such be subject to the GIL. If `"process"` the function will use `multiprocessing` to spawn separate processes that will schedule and evaluate at the timings stated in the configuration.

#### Tile modules

There are a variety of different modules available. Some of them are static and some are dynamic. They can be found here:

##### Time

Mainly for debugging purposes, Displays a single line of text. That line is updated with the current amount of seconds since [Epoch](https://en.wikipedia.org/wiki/Epoch_(computing)).

##### Ctime

Mainly for debugging purposes, Displays a single line of text with a formatted representation of the current time.

##### CPU

Displays a per core CPU load since the last time it queried the system.

##### CPU Load

Shows an overall history of the activity of the processor.

##### RAM

Displays how much of the system's memory is free, available, and in use. Also displays how much memory there is in general.

##### RAM Load

Shows an overall history of the usage of the system memory.

##### GPU

Displays general informatopm about the specified graphics card such as the name (ie. model), total memory, free memory, temperature, powerdraw, fan rpm, clockspeed, and utilization

###### Additional tile Fields

| Field Name | Optional | Default | Options |
|---|---|---|---|
| `gpu_type` | True | `Nvidia` | `Nvidia`, `Intel`, or `AMD` |
| `gpu_index` | True | 0 | Any integer value between 0 and the number of GPUs in the system `[0, N)` |

The same fields apply to all the GPU derivative tiles

##### GPU Memory

Shows an overall history of the usage of the specified GPU's memory.

##### GPU Temperature

Shows an overall history of the usage of the specified GPU's temperature.

##### GPU Power

Shows an overall history of the usage of the specified GPU's powerdraw.

##### GPU Fan

Shows an overall history of the usage of the specified GPU's fan speed.

##### GPU Clock

Shows an overall history of the usage of the specified GPU's clock speed.

##### GPU Utilization

Shows an overall history of the usage of the specified GPU's utilization.

### Sample configuration

The configuration below can be seen in the GIF at the start of the readme.

```json
{
  "screen": {
    "partitions": {
      "type": "tiled",
      "orientation": "vertical",
      "screens": [
        {
          "module": "ctime",
          "border": true,
          "frequency": 1,
          "executed": "thread"
        },
        {
          "partitions": {
            "type": "tiled",
            "orientation": "vertical",
            "screens": [
              {
                "partitions": {
                  "type": "tiled",
                  "orientation": "vertical",
                  "screens": [
                    {
                      "module": "cpu",
                      "border": true,
                      "frequency": 1,
                      "executed": "thread"
                    },
                    {
                      "module": "cpu load",
                      "border": true,
                      "frequency": 5,
                      "executed": "thread"
                    }
                  ]
                }
              },
              {
                "partitions": {
                  "type": "tiled",
                  "orientation": "horizontal",
                  "screens": [
                    {
                      "module": "ram",
                      "border": true,
                      "frequency": 1,
                      "executed": "thread"
                    },
                    {
                      "module": "ram load",
                      "border": true,
                      "frequency": 5,
                      "executed": "thread"
                    }
                  ]
                }
              }
            ]
          }
        }
      ],
      "splits": [0.05]
    }
  }
}

```
