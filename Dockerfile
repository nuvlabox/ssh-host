FROM alpine

RUN apk --no-cache add openssh

COPY ./run_ssh_cmd ./

ENTRYPOINT ["./run_ssh_cmd"]