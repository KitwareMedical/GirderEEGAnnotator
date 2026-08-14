# CHANGELOG

<!-- version list -->

## v1.5.0 (2026-08-14)

### Bug Fixes

- **save annotations**: Fix annotation naming issue
  ([`59c6f7b`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/59c6f7b0e871745271523069bd8a1194205268ce))

### Chores

- **refactor**: Split viewer and portal for future browser UI
  ([`90a182b`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/90a182b637c5a32360ff56526abc0f1de916f9d3))

### Features

- **ui**: Browser as a full page, add breadcrumbs to navigate
  ([`6ca3cd5`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/6ca3cd581160f7b626927c07a7c0e99040bf29de))

- **utils**: Add utils folder with base logic and base ui
  ([`4b6d00f`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/4b6d00f679d005e6c0df810f7dd3e97829ef7fdc))


## v1.4.0 (2026-08-12)

### Features

- **user menu**: Add user menu instead of plain logout button
  ([`b138e9e`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/b138e9e95fa1d527fdf9a1db76f92cb12063c48c))


## v1.3.0 (2026-08-12)

### Documentation

- Adapt pyproject.toml and README
  ([`04ef602`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/04ef6025db2c61607eda4e9d60868873fdbc84ae))

### Features

- **plugin**: Adapt girder database implementation to use GirderBIDS plugin
  ([`5fa0516`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/5fa0516d3acc78693b3753607e7c64343f75c6c7))


## v1.2.0 (2026-07-01)

### Bug Fixes

- **focus**: Focus rca on hover and do not show rca if load failed
  ([`1a3b8a2`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/1a3b8a235109f4cbb0661040fbb25fdff4cd0d2b))

### Chores

- Take reviews into account
  ([`cde2d40`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/cde2d40269f65dca7fe58082cce8475f6a2d164b))

### Features

- **api key**: Enable authentication with api key
  ([`5e99501`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/5e99501066256305258e226c577fe8bcad77871d))

- **auth errors**: Handle authentication errors
  ([`5cda47e`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/5cda47ea1f7c52f7432015216590103111057c8e))

- **authentication**: Add user login and logout
  ([`0470eea`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/0470eeaba47fe0b4eda73d6baf4f47294a94560b))


## v1.1.0 (2026-06-30)

### Bug Fixes

- **annotator**: Remove layout and add ref
  ([`88fb561`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/88fb56187704485972c6677f6ed089a3188e28a4))

### Chores

- Integrate database portal to replace file browser
  ([`77fe48d`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/77fe48d1b4aee50c605413c4d738f10bda7b9d79))

### Continuous Integration

- Fix pre-commit
  ([`ce90b8a`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/ce90b8ad4105958e999a080adcf63fc8c0d53320))

### Features

- **interface**: Add models, database interface and girder implementation
  ([`07f5a5e`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/07f5a5e4a48e441021bf8cc0a2bc93a74a4308e2))

- **metadata**: Add annotation file id as media item metadata
  ([`727f4b7`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/727f4b7700493ac609464966422e257f5bf3e70b))

- **portal**: Add database portal to select data
  ([`aa490b1`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/aa490b1f43e2d24d651a678aba9277dec7c2d68d))

- **save annotations**: Add api to save annotations to EEG item
  ([`97bad9d`](https://github.com/KitwareMedical/GirderEEGAnnotator/commit/97bad9d2b945994061d844979d7666a504859093))


## v1.0.0 (2026-06-17)

- Initial Release
