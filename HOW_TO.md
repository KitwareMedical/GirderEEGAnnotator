Here is an tutorial to run the app from scratch step by step

## How to install Girder with BIDS plugin and import data

```bash
git clone https://github.com/KitwareMedical/GirderBIDS.git
cd GirderBIDS
python -m venv .venv_girder
source .venv_girder/bin/activate
pip install .
```

### 1. Setup the importer CLI

#### Ubuntu 22.04:

```bash
pip install ".[cli]"
```

#### MacOS

```bash
curl -fsSL https://deno.land/install.sh | sh
deno compile -ERWN -o bids-validator jsr:@bids/validator
pip install ".[cli]"
```

#### Windows

BIDS Validation is not supported but you can still use the plugin and the
importer (without validation)

```bash
pip install ".[cli]"
```

### 2. Install MongoDB

If MongoDB is not already installed on your machine, you can install it
following the instructions: https://www.mongodb.com/docs/manual/installation/

#### Ubuntu

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-enterprise-on-ubuntu/#std-label-install-mdb-enterprise-ubuntu
Then:

```bash
sudo systemctl start mongod
```

#### MacOS

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-enterprise-on-os-x/#std-label-install-enterprise-macos
Then:

```bash
brew services start mongodb-community
```

#### Windows

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-enterprise-on-windows/#std-label-install-enterprise-windows

### 3. Serve girder

```bash
girder serve
```

By default, this will serve the Girder client on http://localhost:8080.

### 4. Create admin account

On the Girder client, **Log in** with your admin account or if you don't have
one yet, click on **Register** to create an account. The first account to be
created will be granted admin rights. Email can be factice.

### 5. Create assetstore

Check if your Girder database already has a Filesystem assetstore in **Admin
Console** > **Assetstores**. If not, create a folder (wherever you want) on your
file system and copy its path

```bash
mkdir assetstore
```

Then you can create the assetstore in the **Admin Console** > **Assetstores** >
**Create new Filesystem assetstore**: Assetstore name: assetstore Root
directory: # The path to the folder you just created on your filesystem

### 6. Create API key

On the Girder client, you can access your account settings by clicking on the
top right menu > **My account**. Then choose the **API keys** tab, create a new
key named "My key" and copy it.

### 7. Create a Collection

On the Girder client, you can also create a collection that will be used to load
the datasets and to run the GirderEEGAnnotator app. **Collections** > **Create
Collection**: Name: My Collection

You can then copy its ID either from the URL
(localhost:8080/#collection/{COLLECTION_ID}) or by clicking on "i" to show
collections info.

### 8. Import BIDS Dataset to the database

With the BIDS plugin loaded, you can directly import BIDS Dataset from your
system file to Girder.

In a second terminal, run:

```bash
source .venv_girder/bin/activate
bids-importer --bids_dir {YOUR_LOCAL_BIDS_DATASET_PATH} --api_url http://localhost:8080/api/v1  --api_key {YOUR_API_KEY} --location_id {YOUR_COLLECTION_ID} --location_type collection --use-plugin --extract-metadata
```

## How to install and run GirderEEGAnnotator

In a new terminal,

```bash
git clone https://github.com/KitwareMedical/GirderEEGAnnotator.git
cd GirderEEGAnnotator
python -m venv .venv # either python 3.11 or 3.12
source .venv/bin/activate
pip install .
```

### 1. Setup

Copy the [config.template.yaml](./config.template.yaml) file to a `config.yaml`
file that will be read by the app and fill in the configuration.

Then you can fill in the configuration file:

```yaml
backend:
    type: girder
    api_url: http://localhost:8080/api/v1
    collection_id: {YOUR_COLLECTION_ID}
    api_key: {YOUR_API_KEY} (optional, for dev purposes)
```

### 2. Run the GirderEEGAnnotator app

Run the app on port 8081 because 8080 is already taken by Girder.

```bash
girdereegannotator-cli -p 8081
```

### 3. Browse and annotate

You can browse, search, and filter the datasets available in your collection.

For each dataset, you can:

- Click on a dataset to view its metadata.
- Click **Open** to view all EEGs contained in the dataset.
- Enter text in the search field to filter datasets by name.

Once you have selected a dataset, you can browse and filter its EEGs in the same
way.

For each EEG, you can:

- Click on an EEG to view its metadata and any existing annotation files.
- Click **View** or **New annotation** to open the EEG in the annotator. New
  annotation opens the EEG with an empty annotation file.
- Click on an existing annotation file to open the EEG in the annotator with
  that annotation file loaded.
- Enter text in the search field to filter EEGs by name.
- Use the Status filter to filter EEGs according to their annotation status:
  - **All**: Show all EEGs (default).
  - **To annotate**: Show EEGs that do not have an annotation file yet.
  - **In progress**: Show EEGs with at least one annotation file in progress.
  - **In review**: Show EEGs with at least one annotation file in review.
  - **Done**: Show EEGs with at least three approved annotation files.
- Use the Annotation author filter to further filter the results by author:
  - **Any**: Show all EEGs matching the selected status filter.
  - **Me**: Show EEGs with at least one annotation file created by you and
    matching the selected status filter.
  - **Not Me**: Show EEGs with at least one annotation file created by another
    user and matching the selected status filter.

You can click Refresh, or press F5, to refresh the lists and synchronize them
with the database.

### 4. Annotator rules

A few rules determine what actions are available to users:

- Users can edit and delete their own annotation files while they are **In
  progress**. Once an annotation file reaches another status, it can only be
  viewed.
- Users can withdraw their own annotation files from **In review**.
- Users can review (approve or reject) any **In review** annotation file that
  they did not create.

## How to use TurboJPEG

To use a faster JPEG Encoding you can follow
[these instructions](./README.md#optional-dependencies)

## How to contribute

You can contribute to the GirderEEGAnnotator by following
[these instructions](./CONTRIBUTING.rst)
