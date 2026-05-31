FROM alpine:3.20

RUN apk add --no-cache postgresql16 postgresql16-client su-exec

ENV PGDATA=/var/lib/postgresql/data

COPY infra/docker/postgres-entrypoint.sh /usr/local/bin/postgres-entrypoint.sh
RUN chmod +x /usr/local/bin/postgres-entrypoint.sh

EXPOSE 5432

ENTRYPOINT ["postgres-entrypoint.sh"]
