Wraps the solprop package into a callable microservice.

With docker installed, run `docker build -t solprop_service .` in this directory to build the image.
After, run `docker run -d -p 8081:8081 --name solprop solprop_service` to start the server.
You can check the server outputs with `docker logs solprop`.

A prebuilt version of this image is also available on the ReactionMechanismGenerator DockerHub, which you can download and run to avoid building it yourself: https://hub.docker.com/layers/reactionmechanismgenerator/solprop_microservice/1.0.0/images/sha256-ca48dc8d0b0759a9a750c747758c5e095bf0dfcaae8fe0f64912ce8a91c764ff
