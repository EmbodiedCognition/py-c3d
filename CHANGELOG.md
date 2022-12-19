## [0.5.2] - 19.12.2022

- Fixed numpy dtype deprecated warning (https://github.com/EmbodiedCognition/py-c3d/pull/50)

## [0.5.1] - 22.03.2022

- Fixed installation issues due to maleformated pyproject.toml file
- Scripts are now located withing the c3d folder to avoid packaging issues

## [0.5.0] - 20.03.2022

First version for which we keep changelogs.

### Highlights

- Major improvements to the writer class.
  For details see (https://github.com/EmbodiedCognition/py-c3d/pull/43)

### Added

- Added the ability to have multiple groups with the same name.
  This should not be allowed based on the c3d-spec, but some programs to it anyway.
  In such cases we now rename duplicated groupnames to `{Groupname}{GroupId}`.
  (https://github.com/EmbodiedCognition/py-c3d/pull/45)
- `encode_events()` function is added to the Header to allow header encoded event data to be written to a file
  (note that events generally are written within a Parameter block in 'newer' files).
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)
- A bunch of Tests! generally based on asserting the equivalence of read(write(read(file))) == read(file).
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)
- Major improvements to the writer class.
  For details see (https://github.com/EmbodiedCognition/py-c3d/pull/43)

### Changed

- Various small improvements to the Reader and Writer functionality and the overall coverage of docstrings
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)
- `get_analog_transform()` and get_analog_transform() is factored out of the `read_frames()` function and improved. 
  The transform can now be optionally applied during the read_frame() call.
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)
- `read_frames()` can now optionally check for NaN values in the POINT data (associated frames are marked invalid).
  This should avoid problems for users but it also allows `read(write(read(file))) == read(file)` to be equal.
  It should also provide better support for Vicon systems better (their software example contained NaN values).
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)
- Manager.last_frame logic has been improved to better adhere to the description provided in the manual.
  (https://github.com/EmbodiedCognition/py-c3d/pull/43)

  