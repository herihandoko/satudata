FROM ckan/ckan-base:2.11

# Copy custom initialization scripts
COPY --chown=ckan-sys:ckan-sys ckan/docker-entrypoint.d/* /docker-entrypoint.d/

# Apply any patches needed to CKAN core or any of the built extensions (not the
# runtime mounted ones)
COPY --chown=ckan-sys:ckan-sys ckan/patches ${APP_DIR}/patches

# Install local custom extensions (baked into the image — production-safe).
# Build context must be repo root (see docker-compose.prod.yml).
COPY --chown=ckan-sys:ckan-sys src ${APP_DIR}/src_extensions

USER ckan

# Apply patches first
RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done

# Install local extensions
RUN for ext in $APP_DIR/src_extensions/*/; do \
        if [ -f "$ext/setup.py" ] || [ -f "$ext/pyproject.toml" ]; then \
            echo "Installing $(basename $ext)..." && \
            pip install --no-cache-dir -e "$ext"; \
        fi ; \
    done
