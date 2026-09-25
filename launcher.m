#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#import <sys/socket.h>
#import <netinet/in.h>
#import <arpa/inet.h>
#import <unistd.h>
#import <signal.h>
#import <objc/runtime.h>

@interface AppDelegate : NSObject <NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKDownloadDelegate>
@property (strong, nonatomic) NSWindow *window;
@property (strong, nonatomic) WKWebView *webView;
@property (strong, nonatomic) NSTask *serverTask;
@property (assign, nonatomic) int port;
@end

static int find_free_port(int start_port) {
    for (int port = start_port; port < start_port + 50; port++) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) continue;
        int opt = 1;
        setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = inet_addr("127.0.0.1");
        if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) == 0) {
            close(sock);
            return port;
        }
        close(sock);
    }
    return start_port;
}

@implementation AppDelegate

- (void)setupMenu {
    NSMenu *mainMenu = [[NSMenu alloc] init];
    
    // 1. App Menu
    NSMenuItem *appMenuItem = [[NSMenuItem alloc] init];
    NSMenu *appMenu = [[NSMenu alloc] initWithTitle:@"Sub Studio"];
    [appMenu addItemWithTitle:@"Informazioni su Sub Studio" action:@selector(orderFrontStandardAboutPanel:) keyEquivalent:@""];
    [appMenu addItem:[NSMenuItem separatorItem]];
    [appMenu addItemWithTitle:@"Nascondi Sub Studio" action:@selector(hide:) keyEquivalent:@"h"];
    NSMenuItem *hideOthers = [appMenu addItemWithTitle:@"Nascondi altre" action:@selector(hideOtherApplications:) keyEquivalent:@"h"];
    [hideOthers setKeyEquivalentModifierMask:(NSEventModifierFlagCommand | NSEventModifierFlagOption)];
    [appMenu addItemWithTitle:@"Mostra tutte" action:@selector(unhideAllApplications:) keyEquivalent:@""];
    [appMenu addItem:[NSMenuItem separatorItem]];
    [appMenu addItemWithTitle:@"Esci da Sub Studio" action:@selector(terminate:) keyEquivalent:@"q"];
    [appMenuItem setSubmenu:appMenu];
    [mainMenu addItem:appMenuItem];
    
    // 2. Modifica (Edit) Menu - fondamentale per Cmd+C, Cmd+V, Cmd+X, Cmd+A, Cmd+Z in WKWebView
    NSMenuItem *editMenuItem = [[NSMenuItem alloc] init];
    NSMenu *editMenu = [[NSMenu alloc] initWithTitle:@"Modifica"];
    [editMenu addItemWithTitle:@"Annulla" action:@selector(undo:) keyEquivalent:@"z"];
    [editMenu addItemWithTitle:@"Ripeti" action:@selector(redo:) keyEquivalent:@"Z"];
    [editMenu addItem:[NSMenuItem separatorItem]];
    [editMenu addItemWithTitle:@"Taglia" action:@selector(cut:) keyEquivalent:@"x"];
    [editMenu addItemWithTitle:@"Copia" action:@selector(copy:) keyEquivalent:@"c"];
    [editMenu addItemWithTitle:@"Incolla" action:@selector(paste:) keyEquivalent:@"v"];
    [editMenu addItemWithTitle:@"Seleziona tutto" action:@selector(selectAll:) keyEquivalent:@"a"];
    [editMenuItem setSubmenu:editMenu];
    [mainMenu addItem:editMenuItem];
    
    // 3. Vista Menu
    NSMenuItem *viewMenuItem = [[NSMenuItem alloc] init];
    NSMenu *viewMenu = [[NSMenu alloc] initWithTitle:@"Vista"];
    [viewMenu addItemWithTitle:@"Ricarica" action:@selector(reloadPage:) keyEquivalent:@"r"];
    [viewMenu addItemWithTitle:@"Apri nel Browser predefinito" action:@selector(openInDefaultBrowser:) keyEquivalent:@"b"];
    [viewMenuItem setSubmenu:viewMenu];
    [mainMenu addItem:viewMenuItem];
    
    // 4. Finestra Menu
    NSMenuItem *windowMenuItem = [[NSMenuItem alloc] init];
    NSMenu *windowMenu = [[NSMenu alloc] initWithTitle:@"Finestra"];
    [windowMenu addItemWithTitle:@"Riduci a icona" action:@selector(performMiniaturize:) keyEquivalent:@"m"];
    [windowMenu addItemWithTitle:@"Zoom" action:@selector(performZoom:) keyEquivalent:@""];
    [windowMenuItem setSubmenu:windowMenu];
    [mainMenu addItem:windowMenuItem];
    
    [NSApp setMainMenu:mainMenu];
}

- (void)reloadPage:(id)sender {
    [self.webView reloadFromOrigin];
}

- (void)openInDefaultBrowser:(id)sender {
    if (self.port > 0) {
        NSURL *url = [NSURL URLWithString:[NSString stringWithFormat:@"http://127.0.0.1:%d", self.port]];
        [[NSWorkspace sharedWorkspace] openURL:url];
    }
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    [self setupMenu];
    
    NSRect screenRect = [[NSScreen mainScreen] visibleFrame];
    CGFloat width = MIN(1260, screenRect.size.width - 80);
    CGFloat height = MIN(860, screenRect.size.height - 80);
    NSRect frame = NSMakeRect((screenRect.size.width - width) / 2 + screenRect.origin.x,
                              (screenRect.size.height - height) / 2 + screenRect.origin.y,
                              width, height);
                              
    NSWindowStyleMask style = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable;
    self.window = [[NSWindow alloc] initWithContentRect:frame styleMask:style backing:NSBackingStoreBuffered defer:NO];
    [self.window setTitle:@"Sub Studio"];
    [self.window setMinSize:NSMakeSize(900, 600)];
    self.window.backgroundColor = [NSColor colorWithCalibratedRed:0.024 green:0.031 blue:0.071 alpha:1.0]; // #060812

    WKWebViewConfiguration *config = [[WKWebViewConfiguration alloc] init];
    config.mediaTypesRequiringUserActionForPlayback = WKAudiovisualMediaTypeNone;
    if (@available(macOS 12.3, *)) {
        config.preferences.elementFullscreenEnabled = YES;
    }
    [config.preferences setValue:@YES forKey:@"fullScreenEnabled"];
    
    self.webView = [[WKWebView alloc] initWithFrame:self.window.contentView.bounds configuration:config];
    self.webView.navigationDelegate = self;
    self.webView.UIDelegate = self;
    self.webView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    
    [self.window.contentView addSubview:self.webView];
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
    
    // Schermata di caricamento iniziale
    NSString *loadingHTML = @"<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        "body{background:#060812;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;user-select:none;}"
        ".spinner{width:48px;height:48px;border:3.5px solid #141e36;border-top-color:#00f0ff;border-radius:50%;animation:spin 0.8s linear infinite;margin-bottom:18px;box-shadow:0 0 16px rgba(0,240,255,0.3);}"
        "@keyframes spin{to{transform:rotate(360deg);}}"
        "h2{font-size:18px;font-weight:700;margin:0 0 8px;letter-spacing:-0.02em;background:linear-gradient(135deg,#ffffff,#67e8f9);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}"
        "p{color:#94a3b8;font-size:13px;margin:0;}"
        "</style></head><body><div class='spinner'></div><h2>Avvio Sub Studio...</h2><p>Preparazione dell'ambiente locale in corso</p></body></html>";
    [self.webView loadHTMLString:loadingHTML baseURL:nil];
    
    [self startBackend];
}

- (void)startBackend {
    self.port = find_free_port(8501);
    
    NSString *resourcesPath = [[NSBundle mainBundle] resourcePath];
    NSString *pythonBin = [resourcesPath stringByAppendingPathComponent:@"python/bin/python3"];
    NSString *appDir = [resourcesPath stringByAppendingPathComponent:@"app"];
    NSString *scriptPath = [appDir stringByAppendingPathComponent:@"web_app.py"];
    
    // Cartella dati utente in Filmati (Movies)
    NSString *userDataDir = [NSString stringWithFormat:@"%@/Movies/SubStudio", NSHomeDirectory()];
    NSFileManager *fm = [NSFileManager defaultManager];
    [fm createDirectoryAtPath:[userDataDir stringByAppendingPathComponent:@"web_uploads"] withIntermediateDirectories:YES attributes:nil error:nil];
    [fm createDirectoryAtPath:[userDataDir stringByAppendingPathComponent:@"web_outputs"] withIntermediateDirectories:YES attributes:nil error:nil];
    [fm createDirectoryAtPath:[userDataDir stringByAppendingPathComponent:@"projects"] withIntermediateDirectories:YES attributes:nil error:nil];
    
    // Cartella bin interna al bundle e cartella dati utente
    NSString *bundleBin = [resourcesPath stringByAppendingPathComponent:@"bin"];
    NSString *userBin = [userDataDir stringByAppendingPathComponent:@"bin"];
    [fm createDirectoryAtPath:userBin withIntermediateDirectories:YES attributes:nil error:nil];
    
    // Log file
    NSString *logDir = [NSString stringWithFormat:@"%@/Library/Logs", NSHomeDirectory()];
    [fm createDirectoryAtPath:logDir withIntermediateDirectories:YES attributes:nil error:nil];
    NSString *logFile = [logDir stringByAppendingPathComponent:@"SubStudio.log"];
    [fm createFileAtPath:logFile contents:[NSData data] attributes:nil];
    NSFileHandle *logHandle = [NSFileHandle fileHandleForWritingAtPath:logFile];
    
    if ([fm fileExistsAtPath:pythonBin] && [fm fileExistsAtPath:scriptPath]) {
        self.serverTask = [[NSTask alloc] init];
        self.serverTask.launchPath = pythonBin;
        self.serverTask.arguments = @[scriptPath];
        self.serverTask.currentDirectoryPath = appDir;
        
        NSMutableDictionary *env = [NSMutableDictionary dictionaryWithDictionary:[[NSProcessInfo processInfo] environment]];
        // Priorità assoluta ai binari inclusi nel bundle e gestiti da SubStudio
        env[@"PATH"] = [NSString stringWithFormat:@"%@:%@:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:%@", bundleBin, userBin, env[@"PATH"] ?: @""];
        env[@"PYTHONHOME"] = [resourcesPath stringByAppendingPathComponent:@"python"];
        env[@"PYTHONPATH"] = [NSString stringWithFormat:@"%@:%@/python/lib/python3.12/site-packages", appDir, resourcesPath];
        env[@"LC_ALL"] = @"en_US.UTF-8";
        env[@"SUBSTUDIO_DATA_DIR"] = userDataDir;
        env[@"SUBSTUDIO_PORT"] = [NSString stringWithFormat:@"%d", self.port];
        env[@"SOTTOTITOLATORE_DATA_DIR"] = userDataDir;
        env[@"SOTTOTITOLATORE_PORT"] = [NSString stringWithFormat:@"%d", self.port];
        self.serverTask.environment = env;
        
        if (logHandle) {
            self.serverTask.standardOutput = logHandle;
            self.serverTask.standardError = logHandle;
        }
        
        __weak typeof(self) weakSelf = self;
        self.serverTask.terminationHandler = ^(NSTask *t) {
            if ([t terminationStatus] != 0) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    if (weakSelf.window.isVisible) {
                        NSLog(@"Server terminato con codice: %d", [t terminationStatus]);
                    }
                });
            }
        };
        
        NSError *err = nil;
        if (![self.serverTask launchAndReturnError:&err]) {
            NSLog(@"Errore avvio server: %@", err);
        }
    } else {
        NSLog(@"Percorsi risorse non trovati");
    }
    
    // Polling per caricare la Web UI appena il server è pronto
    [self pollServerAndLoadUI];
}

- (void)pollServerAndLoadUI {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        NSURL *url = [NSURL URLWithString:[NSString stringWithFormat:@"http://127.0.0.1:%d/", self.port]];
        BOOL ready = NO;
        for (int i = 0; i < 100; i++) {
            usleep(250000); // 250ms
            NSMutableURLRequest *req = [NSMutableURLRequest requestWithURL:url];
            req.timeoutInterval = 0.5;
            NSHTTPURLResponse *response = nil;
            NSError *error = nil;
            #pragma clang diagnostic push
            #pragma clang diagnostic ignored "-Wdeprecated-declarations"
            [NSURLConnection sendSynchronousRequest:req returningResponse:&response error:&error];
            #pragma clang diagnostic pop
            if (response && response.statusCode == 200) {
                ready = YES;
                break;
            }
        }
        
        dispatch_async(dispatch_get_main_queue(), ^{
            if (ready) {
                NSURLRequest *req = [NSURLRequest requestWithURL:url cachePolicy:NSURLRequestReloadIgnoringLocalCacheData timeoutInterval:60.0];
                [self.webView loadRequest:req];
            } else {
                NSString *errHTML = @"<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
                    "body{background:#060812;color:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;margin:0;text-align:center;padding:24px;}"
                    ".icon{font-size:48px;margin-bottom:16px;}"
                    "h2{font-size:20px;font-weight:700;margin:0 0 10px;color:#f87171;}"
                    "p{color:#94a3b8;font-size:14px;max-width:480px;line-height:1.5;margin:0 0 20px;}"
                    ".btn{background:linear-gradient(135deg,#00f0ff,#3b82f6);color:#060812;font-weight:700;border:none;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:14px;}"
                    ".log-hint{margin-top:20px;color:#64748b;font-size:12px;font-family:monospace;}"
                    "</style></head><body>"
                    "<div class='icon'>⚠️</div>"
                    "<h2>Impossibile completare l'avvio del server</h2>"
                    "<p>Sub Studio non è riuscito a comunicare con il processo locale in tempo. Verifica che le risorse dell'app siano integre o consulta il registro eventi.</p>"
                    "<button class='btn' onclick='location.reload()'>Riprova</button>"
                    "<div class='log-hint'>Log salvato in: ~/Library/Logs/SubStudio.log</div>"
                    "</body></html>";
                [self.webView loadHTMLString:errHTML baseURL:nil];
            }
        });
    });
}

// WKUIDelegate per il caricamento file (<input type="file">)
- (void)webView:(WKWebView *)webView runOpenPanelWithParameters:(WKOpenPanelParameters *)parameters initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(NSArray<NSURL *> * _Nullable URLs))completionHandler API_AVAILABLE(macos(10.12)) {
    NSOpenPanel *openPanel = [NSOpenPanel openPanel];
    openPanel.allowsMultipleSelection = parameters.allowsMultipleSelection;
    openPanel.canChooseDirectories = parameters.allowsDirectories;
    openPanel.canChooseFiles = YES;
    [openPanel beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse result) {
        if (result == NSModalResponseOK) {
            completionHandler(openPanel.URLs);
        } else {
            completionHandler(nil);
        }
    }];
}

// WKUIDelegate per dialoghi JavaScript Alert e Confirm
- (void)webView:(WKWebView *)webView runJavaScriptAlertPanelWithMessage:(NSString *)message initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(void))completionHandler {
    NSAlert *alert = [[NSAlert alloc] init];
    [alert setMessageText:message];
    [alert addButtonWithTitle:@"OK"];
    [alert beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse returnCode) {
        completionHandler();
    }];
}

- (void)webView:(WKWebView *)webView runJavaScriptConfirmPanelWithMessage:(NSString *)message initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(BOOL result))completionHandler {
    NSAlert *alert = [[NSAlert alloc] init];
    [alert setMessageText:message];
    [alert addButtonWithTitle:@"OK"];
    [alert addButtonWithTitle:@"Annulla"];
    [alert beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse returnCode) {
        completionHandler(returnCode == NSAlertFirstButtonReturn);
    }];
}

// Gestione Download ed aperture esterne
- (void)webView:(WKWebView *)webView decidePolicyForNavigationAction:(WKNavigationAction *)navigationAction preferences:(WKWebpagePreferences *)preferences decisionHandler:(void (^)(WKNavigationActionPolicy, WKWebpagePreferences * _Nonnull))decisionHandler API_AVAILABLE(macos(11.3)) {
    if (navigationAction.shouldPerformDownload) {
        decisionHandler(WKNavigationActionPolicyDownload, preferences);
        return;
    }
    
    // Link esterni (non localhost) si aprono nel browser predefinito di sistema
    if (navigationAction.targetFrame == nil && navigationAction.request.URL) {
        NSString *host = navigationAction.request.URL.host;
        if (host && ![host isEqualToString:@"127.0.0.1"] && ![host isEqualToString:@"localhost"]) {
            [[NSWorkspace sharedWorkspace] openURL:navigationAction.request.URL];
            decisionHandler(WKNavigationActionPolicyCancel, preferences);
            return;
        }
    }
    
    decisionHandler(WKNavigationActionPolicyAllow, preferences);
}

- (void)webView:(WKWebView *)webView decidePolicyForNavigationResponse:(WKNavigationResponse *)navigationResponse decisionHandler:(void (^)(WKNavigationResponsePolicy))decisionHandler API_AVAILABLE(macos(11.3)) {
    if (navigationResponse.canShowMIMEType == NO) {
        decisionHandler(WKNavigationResponsePolicyDownload);
        return;
    }
    if ([navigationResponse.response isKindOfClass:[NSHTTPURLResponse class]]) {
        NSHTTPURLResponse *httpResp = (NSHTTPURLResponse *)navigationResponse.response;
        NSString *disp = httpResp.allHeaderFields[@"Content-Disposition"] ?: httpResp.allHeaderFields[@"content-disposition"];
        if (disp && [disp.lowercaseString containsString:@"attachment"]) {
            decisionHandler(WKNavigationResponsePolicyDownload);
            return;
        }
    }
    decisionHandler(WKNavigationResponsePolicyAllow);
}

- (void)webView:(WKWebView *)webView navigationAction:(WKNavigationAction *)navigationAction didBecomeDownload:(WKDownload *)download API_AVAILABLE(macos(11.3)) {
    download.delegate = self;
}

- (void)webView:(WKWebView *)webView navigationResponse:(WKNavigationResponse *)navigationResponse didBecomeDownload:(WKDownload *)download API_AVAILABLE(macos(11.3)) {
    download.delegate = self;
}

- (void)download:(WKDownload *)download decideDestinationUsingResponse:(NSURLResponse *)response suggestedFilename:(NSString *)suggestedFilename completionHandler:(void (^)(NSURL * _Nullable destination))completionHandler API_AVAILABLE(macos(11.3)) {
    NSString *downloadsDir = [NSSearchPathForDirectoriesInDomains(NSDownloadsDirectory, NSUserDomainMask, YES) firstObject];
    NSString *destPath = [downloadsDir stringByAppendingPathComponent:suggestedFilename];
    
    // Evita sovrascrittura aggiungendo (1), (2)... se il file esiste già
    NSFileManager *fm = [NSFileManager defaultManager];
    if ([fm fileExistsAtPath:destPath]) {
        NSString *baseName = [suggestedFilename stringByDeletingPathExtension];
        NSString *ext = [suggestedFilename pathExtension];
        int counter = 1;
        do {
            NSString *newName = [NSString stringWithFormat:@"%@ (%d).%@", baseName, counter++, ext];
            destPath = [downloadsDir stringByAppendingPathComponent:newName];
        } while ([fm fileExistsAtPath:destPath]);
    }
    
    NSURL *destURL = [NSURL fileURLWithPath:destPath];
    objc_setAssociatedObject(download, "destURL", destURL, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    completionHandler(destURL);
}

- (void)downloadDidFinish:(WKDownload *)download API_AVAILABLE(macos(11.3)) {
    NSURL *destURL = objc_getAssociatedObject(download, "destURL");
    if (destURL) {
        [[NSWorkspace sharedWorkspace] activateFileViewerSelectingURLs:@[destURL]];
    }
}

// Lifecycle & Reopen
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    return YES;
}

- (BOOL)applicationShouldHandleReopen:(NSApplication *)sender hasVisibleWindows:(BOOL)flag {
    if (!flag && self.window) {
        [self.window makeKeyAndOrderFront:nil];
    }
    return YES;
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    if (self.serverTask && [self.serverTask isRunning]) {
        pid_t pid = [self.serverTask processIdentifier];
        [self.serverTask terminate];
        if (pid > 0) {
            kill(pid, SIGTERM);
            kill(-pid, SIGTERM);
        }
        usleep(100000);
    }
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        signal(SIGPIPE, SIG_IGN);
        NSApplication *app = [NSApplication sharedApplication];
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        AppDelegate *delegate = [[AppDelegate alloc] init];
        [app setDelegate:delegate];
        [app run];
    }
    return 0;
}
