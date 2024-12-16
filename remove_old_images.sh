#!/bin/bash

while IFS= read -r line; 
    do
        image_name=$(echo $line | awk '{print $1}')
        image_tag=$(echo $line | awk '{print $2}')
        image_id=$(echo $line | awk '{print $3}')

        if [[ "${image_name}" == "posad97/trading-app" && "${image_tag}" != "latest" ]];
            then
                docker rmi "${image_id}"
        fi

    done < <( docker image ls | tail -n +2)
