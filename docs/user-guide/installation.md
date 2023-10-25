# Installation

Install instructions will be here.

## Docker Quick-start

Do you have a link to a `sky` docker image file? If not, these are not the install
instructions you are looking for. If you do have a link, go ahead and download
the file.  If you are installing on Windows or an Intel-based Mac, you want the
amd64 image.  For installing on more recent Apple Silicon-based Macs, use an
arm64 image.

In addition to the image file, you'll want to download and install
[Docker Desktop](https://www.docker.com) for your computer.  Once it's installed, make
sure it's running (you should be able to open and see Docker's dashboard).

Then, open a console terminal and change to the directory where the docker image
`sky.tar` file has been saved.  It might be named something slightly different from
`sky.tar`, in which case change the filename in the commands you type to match
the filename of the image file you have.  The first step is to run

```shell
docker load --input sky.tar
```

This command may take a few moments to complete, as the content of the downloaded
image file will be imported into docker.  You'll need several free gigabytes of
hard disk space to complete this step, so if you encounter unexplained EOF errors
here that may be the problem.

After the docker image is loaded, you should see a `sky` image in the docker desktop
dashboard.  If you can see it, you should then be able to start a container with
this image using the following command:

=== "Mac/Linux"

    ``` bash
    docker run -p 8899:8899 --rm --volume "$(pwd)":/tmp/workplace/work sky:latest
    ```

=== "Windows"

    ``` bash
    docker run -p 8899:8899 --rm --volume "%cd%":/tmp/workplace/work sky:latest
    ```

Within this command, we have:

- `-p 8899:8899` tells docker to expose the container's port 8899 (which has been
  configured to be the port served by Jupyter Lab) to localhost.
- `--rm` means to remove the container when it exits, so there isn't an
  extraneous container image file left on your file system.
- `--volume "...":/tmp/workplace/work` makes the current working directory
  available inside Jupyter Lab in a directory named `work` (the container has
  been configured with `/tmp/workplace` as the base location for Jupyter).
- `sky:latest` tells Docker to use the latest version of the user image
  that was installed in the `docker load` step above.  If your installed
  docker image (as shown in the Docker Dashboard) has a different name than
  `sky` then change the command to give the corrent image name.
