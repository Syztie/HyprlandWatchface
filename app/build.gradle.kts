plugins {
    alias(libs.plugins.android.application)
}

android {
    enableKotlin = false
    namespace = "io.github.syztie.hyprlandwatchface"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.syztie.hyprlandwatchface"
        // Weather data needs Watch Face Format version 2, available from
        // Wear OS 5 (API 34) onwards.
        minSdk = 34
        targetSdk = 36
        // CI passes the run number so every test build installs over the last.
        versionCode = (project.findProperty("versionCode") as String?)?.toInt() ?: 1
        versionName = (project.findProperty("versionName") as String?) ?: "0.2.0-dev"
    }

    signingConfigs {
        // Fixed debug key checked into the repo, so APKs built locally and
        // in CI can be installed over each other without uninstalling.
        getByName("debug") {
            storeFile = rootProject.file("keystore/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debug")
        }
        release {
            isMinifyEnabled = false
            // Resources are only referenced from watchface.xml, never from
            // code, so shrinking would remove them.
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}
