package org.nx2a.nfshpr.launcher;

import android.app.Activity;
import android.app.ActivityManager;
import android.app.NativeActivity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.opengl.EGL14;
import android.opengl.EGLConfig;
import android.opengl.EGLContext;
import android.opengl.EGLDisplay;
import android.opengl.EGLSurface;
import android.opengl.GLES20;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final String GAME_DIR = "/sdcard/Games/NFSHPR";
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN
        );
        if (Build.VERSION.SDK_INT >= 28) {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            getWindow().setAttributes(lp);
        }

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#0d1015"));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.setVerticalScrollBarEnabled(false);
        webView.setHorizontalScrollBarEnabled(false);

        WebSettings ws = webView.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setDomStorageEnabled(true);
        ws.setAllowFileAccess(true);
        ws.setBuiltInZoomControls(false);
        ws.setDisplayZoomControls(false);
        ws.setUseWideViewPort(true);
        ws.setLoadWithOverviewMode(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String s = uri != null ? uri.toString() : "";
                if (s.startsWith("http://") || s.startsWith("https://")) {
                    openExternalUrl(s);
                    return true;
                }
                return false;
            }
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url != null && (url.startsWith("http://") || url.startsWith("https://"))) {
                    openExternalUrl(url);
                    return true;
                }
                return false;
            }
        });
        webView.addJavascriptInterface(new LauncherBridge(), "AndroidBridge");
        setContentView(webView);

        hideSystemUi();
        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemUi();
    }

    @Override
    public void onBackPressed() {
        if (webView != null) {
            webView.evaluateJavascript("window.onAndroidBack && window.onAndroidBack()", null);
        } else {
            super.onBackPressed();
        }
    }

    private void openExternalUrl(String url) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        } catch (Throwable ignored) {}
    }

    private void hideSystemUi() {
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN
        );
    }

    private File getAppFilesDir() {
        File d = getExternalFilesDir(null);
        if (d == null) d = getFilesDir();
        if (!d.exists()) d.mkdirs();
        return d;
    }

    private static String readTextFile(File f) {
        if (f == null || !f.exists() || !f.canRead()) return "";
        try (FileInputStream fis = new FileInputStream(f);
             ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = fis.read(buf)) > 0) bos.write(buf, 0, n);
            return bos.toString("UTF-8");
        } catch (Exception e) {
            return "";
        }
    }

    private static boolean writeTextFile(File f, String content) {
        try {
            File p = f.getParentFile();
            if (p != null && !p.exists()) p.mkdirs();
            try (FileOutputStream fos = new FileOutputStream(f, false)) {
                fos.write(content.getBytes(StandardCharsets.UTF_8));
                fos.flush();
            }
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private String cachedGpuRenderer = null;
    private String cachedGpuVendor = null;

    private void detectGpuStrings() {
        if (cachedGpuRenderer != null) return;
        cachedGpuRenderer = "";
        cachedGpuVendor = "";
        try {
            EGLDisplay dpy = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);
            if (dpy == null || dpy == EGL14.EGL_NO_DISPLAY) return;
            int[] ver = new int[2];
            if (!EGL14.eglInitialize(dpy, ver, 0, ver, 1)) return;
            int[] cfgSpec = {
                EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
                EGL14.EGL_SURFACE_TYPE, EGL14.EGL_PBUFFER_BIT,
                EGL14.EGL_RED_SIZE, 8, EGL14.EGL_GREEN_SIZE, 8, EGL14.EGL_BLUE_SIZE, 8,
                EGL14.EGL_NONE
            };
            EGLConfig[] cfgs = new EGLConfig[1];
            int[] numCfg = new int[1];
            if (EGL14.eglChooseConfig(dpy, cfgSpec, 0, cfgs, 0, 1, numCfg, 0) && numCfg[0] > 0) {
                EGLConfig cfg = cfgs[0];
                int[] ctxAttr = { EGL14.EGL_CONTEXT_CLIENT_VERSION, 2, EGL14.EGL_NONE };
                EGLContext ctx = EGL14.eglCreateContext(dpy, cfg, EGL14.EGL_NO_CONTEXT, ctxAttr, 0);
                int[] pbufAttr = { EGL14.EGL_WIDTH, 1, EGL14.EGL_HEIGHT, 1, EGL14.EGL_NONE };
                EGLSurface surf = EGL14.eglCreatePbufferSurface(dpy, cfg, pbufAttr, 0);
                if (ctx != null && ctx != EGL14.EGL_NO_CONTEXT && surf != null && surf != EGL14.EGL_NO_SURFACE) {
                    if (EGL14.eglMakeCurrent(dpy, surf, surf, ctx)) {
                        String r = GLES20.glGetString(GLES20.GL_RENDERER);
                        String v = GLES20.glGetString(GLES20.GL_VENDOR);
                        if (r != null) cachedGpuRenderer = r;
                        if (v != null) cachedGpuVendor = v;
                    }
                    EGL14.eglMakeCurrent(dpy, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT);
                }
                if (surf != null && surf != EGL14.EGL_NO_SURFACE) EGL14.eglDestroySurface(dpy, surf);
                if (ctx != null && ctx != EGL14.EGL_NO_CONTEXT) EGL14.eglDestroyContext(dpy, ctx);
            }
            EGL14.eglTerminate(dpy);
        } catch (Throwable ignored) {}
    }

    public class LauncherBridge {
        @JavascriptInterface
        public String getStatus() {
            try {
                detectGpuStrings();
                JSONObject o = new JSONObject();
                boolean storage = Build.VERSION.SDK_INT < 30 || Environment.isExternalStorageManager();
                boolean romfsOk = new File(GAME_DIR + "/RomFS").isDirectory();
                boolean hasKgsl = new File("/dev/kgsl-3d0").exists();
                String socModel = Build.HARDWARE != null ? Build.HARDWARE : "";
                String socMaker = "";
                if (Build.VERSION.SDK_INT >= 31) {
                    if (Build.SOC_MODEL != null && !Build.SOC_MODEL.isEmpty() && !"unknown".equalsIgnoreCase(Build.SOC_MODEL)) {
                        socModel = Build.SOC_MODEL;
                    }
                    if (Build.SOC_MANUFACTURER != null && !"unknown".equalsIgnoreCase(Build.SOC_MANUFACTURER)) {
                        socMaker = Build.SOC_MANUFACTURER;
                    }
                }
                String gpuLow = cachedGpuRenderer.toLowerCase();
                String makerLow = socMaker.toLowerCase();
                String profile;
                if (gpuLow.contains("mali") || gpuLow.contains("immortalis") || makerLow.contains("mediatek") || socModel.toLowerCase().startsWith("mt")) {
                    profile = "mali_mtk";
                } else if (gpuLow.contains("adreno") && (gpuLow.contains("8") && gpuLow.matches(".*adreno[^0-9]*8[0-9]{2}.*"))) {
                    profile = "adreno_sys";
                } else if (gpuLow.contains("adreno") || hasKgsl || makerLow.contains("qualcomm")) {
                    profile = "adreno_turnip";
                } else {
                    profile = "system";
                }
                o.put("storage", storage);
                o.put("romfs", romfsOk);
                o.put("gameInstalled", true);
                o.put("device", Build.MODEL);
                o.put("android", Build.VERSION.RELEASE);
                o.put("gpuRenderer", cachedGpuRenderer);
                o.put("gpuVendor", cachedGpuVendor);
                o.put("socModel", socModel);
                o.put("socMaker", socMaker);
                o.put("cpuCores", Runtime.getRuntime().availableProcessors());
                o.put("hasKgsl", hasKgsl);
                o.put("gpuProfile", profile);
                return o.toString();
            } catch (Exception e) {
                return "{}";
            }
        }

        @JavascriptInterface
        public void requestStoragePermission() {
            if (Build.VERSION.SDK_INT >= 30) {
                try {
                    Intent i = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                    i.setData(Uri.parse("package:" + getPackageName()));
                    startActivity(i);
                } catch (Exception e) {
                    startActivity(new Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION));
                }
            }
        }

        @JavascriptInterface
        public String loadConfig() {
            try {
                File appDir = getAppFilesDir();
                String env = readTextFile(new File(GAME_DIR + "/env.txt"));
                if (env.isEmpty()) env = readTextFile(new File(appDir, "env.txt"));
                String settings = readTextFile(new File(GAME_DIR + "/settings.txt"));
                if (settings.isEmpty()) settings = readTextFile(new File(appDir, "settings.txt"));
                String ui = readTextFile(new File(appDir, "launcher_ui.json"));
                if (ui.isEmpty()) ui = readTextFile(new File(GAME_DIR + "/launcher_ui.json"));

                JSONObject o = new JSONObject();
                o.put("env", env);
                o.put("settings", settings);
                o.put("ui", ui);
                return o.toString();
            } catch (Exception e) {
                return "{}";
            }
        }

        @JavascriptInterface
        public String saveConfig(String envText, String settingsText, String uiJson) {
            File appDir = getAppFilesDir();
            boolean okApp = writeTextFile(new File(appDir, "env.txt"), envText)
                && writeTextFile(new File(appDir, "settings.txt"), settingsText);
            writeTextFile(new File(appDir, "launcher_ui.json"), uiJson);

            // Also mirror to /sdcard/Games/NFSHPR/ when storage access is granted
            writeTextFile(new File(GAME_DIR + "/env.txt"), envText);
            writeTextFile(new File(GAME_DIR + "/settings.txt"), settingsText);
            writeTextFile(new File(GAME_DIR + "/launcher_ui.json"), uiJson);

            return okApp ? "ok" : "err:Не удалось записать конфиг в " + appDir.getAbsolutePath();
        }

        @JavascriptInterface
        public String launchGame(String envText, String settingsText, String uiJson) {
            String saved = saveConfig(envText, settingsText, uiJson);
            if (saved.startsWith("err:")) return saved;
            try {
                ActivityManager am = (ActivityManager) getSystemService(Context.ACTIVITY_SERVICE);
                if (am != null && am.getRunningAppProcesses() != null) {
                    for (ActivityManager.RunningAppProcessInfo p : am.getRunningAppProcesses()) {
                        if (p.processName != null && p.processName.endsWith(":game")) {
                            android.os.Process.killProcess(p.pid);
                        }
                    }
                }
            } catch (Exception ignored) {}
            Intent intent = new Intent(MainActivity.this, NativeActivity.class);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivity(intent);
            return "ok";
        }

        @JavascriptInterface
        public void openUrl(String url) {
            if (url != null && (url.startsWith("http://") || url.startsWith("https://"))) {
                runOnUiThread(() -> openExternalUrl(url));
            }
        }

        @JavascriptInterface
        public String copyLog() {
            File logFile = new File(getAppFilesDir(), "log.txt");
            String txt = readTextFile(logFile);
            if (txt.isEmpty()) {
                return "err:Лог пока пуст (" + logFile.getAbsolutePath() + ")";
            }
            if (txt.length() > 262144) {
                txt = txt.substring(txt.length() - 262144);
            }
            final String clip = txt;
            runOnUiThread(() -> {
                ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                if (cm != null) {
                    cm.setPrimaryClip(ClipData.newPlainText("NFSHPR log", clip));
                }
            });
            int lines = clip.split("\n").length;
            return "ok:" + lines + ":" + clip.length();
        }
    }
}
