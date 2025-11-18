# Documentation for Gopher Server config files

Gopher Server config files are a collection of blocks that determine what and how your Gopher server serves its content.

At the highest level, it is a list of servers. Thus 

```json
[
    {
        "host": "localhost",
        "port": 70,
        "serve": {
            "root": "./serve"
        }
    },
    {
        "host": "localhost",
        "port": 71,
        "serve": {
            "root": "./serve2"
        }
    },
]
```
Is 2 servers that on port 70 and 71 serves the ```./serve``` and ```./serve2``` folder respectively.

## Servers

Server configs must have a "host", "port", and "serve". "serve" must contain a root object, described later.

```json
...
{
    "host": "localhost",
    "port": 70,
    "serve": {
        "selectors": {
            "about": {
                "root" {
                    "directory": "/homr/faraz/about"
                }
            },
            "default": {
                "root" {
                    "directory": "./serve"
                }
            }
        }
    }
}
```

Thus when visiting ```gopher://localhost/1/about``` we get served what we expect from the corrosponding root object. The "default" selector must always exist for when no existing selector applies.

# Root Object

This describes what exactly you want to serve. Providing a string serves that path with default configs. To adust configs from defaults you must use a JSON object.

```json
...
    {
        "root": {
            "directory": "./serve",
            "search": true
        }
    }
...
```

The object itself is the type of root block (e.g. "root" or "selectors") with an enclosed object containing arguments.

## "root"

The most fundamental type is the "root" type, that simply serves a directory.

Possible arguments for "root" type the following:

### "search"

Adds an additional menu option at the top with as a /search submenu that allows filename-searching of contents in that menu. Default is false.

### "search_recursive"

Only active if search is true. Whether fulltext searching should be recursive. Default is false.

### "override_type"

Forces the type of all contents of root to be that type (overriding file extension based prediction). Expects a single character. Default is "null" (inactive).

## "selectors"

This allows you to compose root blocks based on Gopher selector prefixes. Object keys should be prefixes and values should be root blocks. When stacking selector blocks, note that the prefix from the first is removed when evaluating the second. 