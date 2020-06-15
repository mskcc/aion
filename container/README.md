Image that by default builds from "master" branch.

Can provide a branch, tag, or commit hash by using COMMIT_VERSION ARG.

For example:

docker build --build-arg COMMIT_VERSION="97b6684a039bc0285fe970b007ae4407233527d4" -f aion/Dockerfile .
