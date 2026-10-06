# Build, check and deploy the Hyprland watch face.
#
#   make build        assemble the debug APK with Gradle
#   make validate     XSD validation (WFF v2), memory footprint, layout audit
#   make install      install the APK on the watch via adb (WLAN)
#   make screenshot   pull a screenshot from the watch into screenshots/
#   make preview      render offline previews into build/preview/
#   make generate     regenerate res/raw/watchface.xml from watchface/
#   make icons        generate, then render the theme icons
#   make docs         check that README.md and README.de.md match in structure

WFF_VERSION   := 2
WATCHFACE_XML := app/src/main/res/raw/watchface.xml
APK           := app/build/outputs/apk/debug/app-debug.apk
PACKAGE       := io.github.syztie.hyprlandwatchface
TOOLS_BIN     := tools/bin
ADB           ?= adb
PYTHON        ?= python3

.PHONY: build generate check-generated icons docs validate validate-xml memory audit install screenshot preview tools clean

build:
	./gradlew :app:assembleDebug

generate:
	$(PYTHON) tools/build_watchface.py

check-generated:
	$(PYTHON) tools/build_watchface.py --check

THEMES = $(shell $(PYTHON) -c "import json;[print(i, t['id']) for i, t in enumerate(json.load(open('watchface/themes.json'))['themes'])]")

# Theme icons for the theme picker and flavors, rendered offline from the
# freshly generated XML (so a new theme in themes.json gets a real icon).
icons: generate
	@set -- $(THEMES); while [ $$# -ge 2 ]; do \
	  echo "theme $$1: app/src/main/res/drawable/theme_$$2.png"; \
	  $(PYTHON) tools/render_preview.py --theme $$1 --size 192 -o app/src/main/res/drawable/theme_$$2.png; \
	  shift 2; \
	done

tools: $(TOOLS_BIN)/wff-validator.jar $(TOOLS_BIN)/memory-footprint.jar

$(TOOLS_BIN)/wff-validator.jar $(TOOLS_BIN)/memory-footprint.jar:
	tools/fetch-tools.sh

validate: check-generated validate-xml memory audit docs

validate-xml: $(TOOLS_BIN)/wff-validator.jar
	java -jar $(TOOLS_BIN)/wff-validator.jar $(WFF_VERSION) $(WATCHFACE_XML)

memory: $(TOOLS_BIN)/memory-footprint.jar $(APK)
	java -jar $(TOOLS_BIN)/memory-footprint.jar --watch-face $(APK) \
		--schema-version $(WFF_VERSION) --ambient-limit-mb 10 --active-limit-mb 100 \
		--apply-v1-offload-limitations --estimate-optimization

docs:
	$(PYTHON) tools/check_readmes.py

audit:
	$(PYTHON) tools/audit.py
	$(PYTHON) tools/test_expressions.py

$(APK):
	./gradlew :app:assembleDebug

install: $(APK)
	$(ADB) install -r $(APK)
	@echo "Now pick the watch face on the watch: long-press the current face, swipe to 'Hyprland'."

screenshot:
	@mkdir -p screenshots
	$(ADB) exec-out screencap -p > screenshots/watch-$$(date +%Y%m%d-%H%M%S).png
	@ls -t screenshots/*.png | head -1

preview:
	@mkdir -p build/preview
	@set -- $(THEMES); while [ $$# -ge 2 ]; do \
	  $(PYTHON) tools/render_preview.py --theme $$1 -o build/preview/active-$$1.png; \
	  $(PYTHON) tools/render_preview.py --theme $$1 --ambient -o build/preview/ambient-$$1.png; \
	  shift 2; \
	done

clean:
	./gradlew clean
	rm -rf build/preview
