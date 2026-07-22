# GirderEGGAnnotator

![GirderEGGAnnotator](https://github.com/user-attachments/assets/37796cb5-840f-4feb-885c-87b1ff2963ea)

Works only on Linux/Mac, not on Windows.

## Create environment and install dependencies

```
python -m venv .venv
source env/bin/activate
pip install .
```

### Contributing

Install development dependencies

```
pip install -e ".[dev]"
```

### Optional dependencies

---

Faster Jpeg encoding using TurboJPEG.

**macOS system install**

```
# macOS
brew install jpeg-turbo
```

**Windows install**

Download and install from GitHub:
https://github.com/libjpeg-turbo/libjpeg-turbo/releases

**Linux install**

```
# RHEL/CentOS/Fedora
# YUM doc: https://libjpeg-turbo.org/Downloads/YUM
# Ubuntu
apt-get install libturbojpeg
```

Once your system is ready, you can install the dependencies:

```
pip install ".[turbo]"
```

## Run trame application

### Configuration file

Copy the [config.template.yaml](./config.template.yaml) file to a config.yaml
file that will be read by the app and fill in the configuration. This
configuration file holds the style of the application and the configuration of
the Girder backend. This application expects Girder running with the GirderBIDS
plugin available [here](https://github.com/KitwareMedical/GirderBIDS)

```
# Clone the library
cd ..
git clone https://github.com/KitwareMedical/GirderBIDS.git
cd GirderBIDS
```

Then, you can follow the plugin instructions to run your Girder backend.

Then you can fill in the configuration file:

```
backend:
    type: girder
    api_url: the api URL of your girder. For instance : http://localhost:8080/api/v1
    api_key: the API key of a girder user (optional, for dev purposes)
```

### Run the EEGAnnotator

```
girdereegannotator
```

To test the application, you can try to use the
[_example.neonatal_](https://github.com/KitwareMedical/GirderEGGAnnotator/releases/download/untagged-149f037e2bbb82651e1a/example.neonatal)
file provided in the assets. You can add `--server` to your command line to
prevent your browser from opening and `--port` to specify the port the server
should listen to, default is 8080.

## Acknowledgement

This work was supported by the Agence Nationale de la Recherche (Grant
ANR-22-CE45-0034).
