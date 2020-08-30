# Observ

A simple curses based system monitor similar to that of glances and htop

## Requirements

- [Blessed](https://github.com/jquast/blessed)

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

#### tile Fields

| Field Name | Optional | Applies to | Default | Options |
|---|---|---|---|---|
| `module` | False | All | `N/A` | See below |
| `border` | True | All | False | True, False, or an array of all the different characters in the border |
| `title` | True | All | `""` | Any string |
| `frequency` | True | Dynamic modules | 1 | Any integer |
| `executed` | True | Dynamic modules | `"native"` | `"native"`, `"thread"`, or `"process"` |

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

### Sample configuration

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
