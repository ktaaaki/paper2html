#!/bin/bash

MOUNT_PATH=./paper_cache
USER_NAME=paperuser

# Check the permissions of the bind mount.
if [[ -d "${MOUNT_PATH}" ]]; then
    USER_UID=$(stat ${MOUNT_PATH} -c "%u")
    USER_GID=$(stat ${MOUNT_PATH} -c "%g")
    # Make sure that the USER is root or non-root user.
    if [[ "${USER_UID}" != "0" ]]; then
        # Creat the new user.
        if [[ -z "$(getent passwd "${USER_NAME}")" ]]; then
            groupadd -g ${USER_GID} ${USER_NAME}
            useradd -m -s /bin/bash -u ${USER_UID} -g ${USER_NAME} ${USER_NAME}
        fi
        export USER_NAME
    else
        export USER_NAME=
    fi
else
    export USER_NAME=
fi

exec "$@"