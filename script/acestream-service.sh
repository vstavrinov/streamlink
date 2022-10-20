#!/bin/bash -e

VERSION=$(versioningit)
CONTENT=$(echo -n $VERSION | base64 -w0)

ENDPOINT=vstavrinov/streamlink-service/contents
curl                                                    \
    -H "Accept: application/vnd.github.v3+json"         \
    -H "Authorization: token $STREAMLINK_SERVICE_TOKEN" \
    https://api.github.com/repos/$ENDPOINT/streamlink-version

curl -X POST                                            \
    -H "Accept: application/vnd.github.v3+json"         \
    -H "Authorization: token $STREAMLINK_SERVICE_TOKEN" \
    -d '{"message": "Update streamlink to '$VERSION'",
         "content": "'$CONTENT'",
         "sha": "4bc3c67a4544a45141f13e24e91e605268577a2a"
      }'                                                \
    https://api.github.com/repos/$ENDPOINT/streamlink-version

ENDPOINT=vstavrinov/streamlink-service/actions/workflows/main.yml
COMMIT=$(git rev-parse --short $GITHUB_SHA)
curl -X POST                                            \
    -H "Accept: application/vnd.github.v3+json"         \
    -H "Authorization: token $STREAMLINK_SERVICE_TOKEN" \
    -d '{"ref": "master",
         "inputs":
           {"streamlink": "'$COMMIT'"}
      }'                                                \
    https://api.github.com/repos/$ENDPOINT/dispatches
