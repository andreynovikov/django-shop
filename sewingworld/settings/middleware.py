MIDDLEWARE = (
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # first, to see the 500 made of an exception in any other middleware
    'errors.middleware.ErrorCaptureMiddleware',
    # X-Content-Type-Options, Referrer-Policy and Cross-Origin-Opener-Policy on every response, including errors.
    # nginx redirects to HTTPS, so SECURE_SSL_REDIRECT stays off.
    'django.middleware.security.SecurityMiddleware',
    # before everything that uses the site, the client address or the session
    'sewingworld.middleware.FrontendKeyMiddleware',
    'sewingworld.middleware.BlockedIpMiddleware',
    'sewingworld.middleware.SiteDetectionMiddleware',
    # 'sewingworld.middleware.ProcessExceptionMiddleware',
    'sewingworld.middleware.CookieRenameMiddleware',
    'sewingworld.middleware.PrivateApiCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'drf_api_logger.middleware.api_logger_middleware.APILoggerMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
)
