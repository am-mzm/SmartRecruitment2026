import { Configuration, PopupRequest, LogLevel, PublicClientApplication } from "@azure/msal-browser";

export const msalConfig: Configuration = {
    auth: {
        clientId: process.env.REACT_APP_CLIENT_ID || "",
        authority: process.env.REACT_APP_AUTHORITY || "", 
        redirectUri: process.env.REACT_APP_REDIRECT_URI || "",
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    },
    system: {
        loggerOptions: {
            loggerCallback: (level, message, containsPii) => {
                if (containsPii) {
                    return;
                }
                switch (level) {
                    case LogLevel.Error:
                        console.error(message);
                        break;
                    case LogLevel.Info:
                        console.info(message);
                        break;
                    case LogLevel.Verbose:
                        console.debug(message);
                        break;
                    case LogLevel.Warning:
                        console.warn(message);
                        break;
                }
            },
            piiLoggingEnabled: false, 
            logLevel: LogLevel.Verbose, 
        },
    },
};

export const loginRequest: PopupRequest = {
    scopes: ["User.Read", "openid", "profile", "email", "offline_access"],
};

// Will remove soon until I have found an alternative
// export const graphConfig = {
//     graphMeEndpoint: "https://graph.microsoft.com/v1.0/me",
//     graphMeMemberOfEndpoint: "https://graph.microsoft.com/v1.0/me/memberOf",
//     // graphGroupEndpoint: "https://graph.microsoft.com/v1.0/groups"    
// };