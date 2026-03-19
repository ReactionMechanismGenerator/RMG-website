Wraps the solprop package into a callable microservice.

With docker installed, run `docker build -t solprop_service .` in this directory to build the image.
After, run `docker run -d -p 8081:8081 --name solprop solprop_service` to start the server.
You can check the server outputs with `docker logs solprop`.

A prebuilt version of this image is also available on the ReactionMechanismGenerator DockerHub.
