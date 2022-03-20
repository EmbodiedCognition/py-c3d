## [0.5.0] - 

First version for which we keep changelogs.

### Added

- Added the ability to have multiple groups with the same name.
  This should not be allowed based on the c3d-spec, but some programs to it anyway.
  In such cases we now rename duplicated groupnames to `{Groupname}{GroupId}`.
  (https://github.com/EmbodiedCognition/py-c3d/pull/45)
  