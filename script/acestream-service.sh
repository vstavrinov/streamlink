#!/bin/bash -e

VERSION=$(versioningit)
CONTENT=$(echo -n $VERSION | base64 -w0)

ENDPOINT=vstavrinov/streamlink-service/contents
SHA="$(curl                                             \
    -H "Accept: application/vnd.github.v3+json"         \
    -H "Authorization: token $STREAMLINK_SERVICE_TOKEN" \
    https://api.github.com/repos/$ENDPOINT/streamlink-version |
    awk -F\" '/"sha":/ {print $4}')"

echo SHA=$SHA
curl -X POST                                            \
    -H "Accept: application/vnd.github.v3+json"         \
    -H "Authorization: token $STREAMLINK_SERVICE_TOKEN" \
    -d '{"message": "Update streamlink to '$VERSION'",
         "sha": "'$SHA'",
         "content": "'$CONTENT'"
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
