# Build, check and deploy the Hyprland watch face.
#
#   make build        assemble the debug APK with Gradle
#   make validate     XSD validation (WFF v2), memory footprint, layout audit
#   make install      install the APK on the watch via adb (WLAN)
#   make screenshot   pull a screenshot from the watch into screenshots/
#   make preview      render offline previews into build/preview/

WFF_VERSION   := 2
WATCHFACE_XML := app/src/main/res/raw/watchface.xml
APK           := app/build/outputs/apk/debug/app-debug.apk
PACKAGE       := io.github.syztie.hyprlandwatchface
TOOLS_BIN     := tools/bin
ADB           ?= adb
PYTHON        ?= python3

.PHONY: build validate validate-xml memory audit install screenshot preview tools clean

build:
	./gradlew :app:assembleDebug

tools: $(TOOLS_BIN)/wff-validator.jar $(TOOLS_BIN)/memory-footprint.jar

$(TOOLS_BIN)/wff-validator.jar $(TOOLS_BIN)/memory-footprint.jar:
	tools/fetch-tools.sh

validate: validate-xml memory audit

validate-xml: $(TOOLS_BIN)/wff-validator.jar
	java -jar $(TOOLS_BIN)/wff-validator.jar $(WFF_VERSION) $(WATCHFACE_XML)

memory: $(TOOLS_BIN)/memory-footprint.jar $(APK)
	java -jar $(TOOLS_BIN)/memory-footprint.jar --watch-face $(APK) \
		--schema-version $(WFF_VERSION) --ambient-limit-mb 10 --active-limit-mb 100 \
		--apply-v1-offload-limitations --estimate-optimization

audit:
	$(PYTHON) tools/audit.py

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
	$(PYTHON) tools/render_preview.py -o build/preview/active.png
	$(PYTHON) tools/render_preview.py --ambient -o build/preview/ambient.png

clean:
	./gradlew clean
	rm -rf build/preview
