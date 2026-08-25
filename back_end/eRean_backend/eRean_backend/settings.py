from datetime import timedelta

from pathlib import Path


import dj_database_url

import environ

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


env = environ.Env()

environ.Env.read_env(BASE_DIR / '.env')


DEBUG = env.bool('DEBUG', default=False)


SECRET_KEY = env('SECRET_KEY', default='')

if not SECRET_KEY:

    if DEBUG:

        SECRET_KEY = 'django-insecure-dev-only-do-not-use-in-production'

    else:

        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is False.')


ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


RENDER_EXTERNAL_HOSTNAME = env('RENDER_EXTERNAL_HOSTNAME', default='')

if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:

    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


if DEBUG:

    ALLOWED_HOSTS = ['*']


AUTH_USER_MODEL = 'users.User'


INSTALLED_APPS = [

    'django.contrib.admin',

    'django.contrib.auth',

    'django.contrib.contenttypes',

    'django.contrib.sessions',

    'django.contrib.messages',

    'django.contrib.staticfiles',

    'rest_framework',

    'rest_framework_simplejwt',

    'rest_framework_simplejwt.token_blacklist',

    'django_filters',

    'corsheaders',

    'users',

    'courses',

    'assignments',

    'enrollments',

    'attendance',

    'discussions',

    'notifications',

]


MIDDLEWARE = [

    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'corsheaders.middleware.CorsMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]


ROOT_URLCONF = 'eRean_backend.urls'


TEMPLATES = [

    {

        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {

            'context_processors': [

                'django.template.context_processors.request',

                'django.contrib.auth.context_processors.auth',

                'django.contrib.messages.context_processors.messages',

            ],

        },

    },

]


WSGI_APPLICATION = 'eRean_backend.wsgi.application'


DATABASES = {

    'default': {

        'ENGINE': 'django.db.backends.postgresql',

        'NAME': env('DB_NAME', default='eRean_DB'),

        'USER': env('DB_USER', default='postgres'),

        'PASSWORD': env('DB_PASSWORD', default=''),

        'HOST': env('DB_HOST', default='localhost'),

        'PORT': env('DB_PORT', default='5432'),

    }

}


DATABASE_URL = env('DATABASE_URL', default='')

if DATABASE_URL:

    DATABASES['default'] = dj_database_url.parse(

        DATABASE_URL,

        conn_max_age=600,

        conn_health_checks=True,

        ssl_require=env.bool('DB_SSL_REQUIRE', default=not DEBUG),

    )


AUTH_PASSWORD_VALIDATORS = [

    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},

    {

        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',

        'OPTIONS': {'min_length': 8},

    },

    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},

    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},

]


REST_FRAMEWORK = {

    'DEFAULT_AUTHENTICATION_CLASSES': (

        'rest_framework_simplejwt.authentication.JWTAuthentication',

    ),

    'DEFAULT_PERMISSION_CLASSES': (

        'rest_framework.permissions.IsAuthenticated',

    ),

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',

    'PAGE_SIZE': 20,

    'DEFAULT_FILTER_BACKENDS': [

        'django_filters.rest_framework.DjangoFilterBackend',

        'rest_framework.filters.SearchFilter',

        'rest_framework.filters.OrderingFilter',

    ],

    'DEFAULT_THROTTLE_CLASSES': [

        'rest_framework.throttling.AnonRateThrottle',

        'rest_framework.throttling.UserRateThrottle',

        'rest_framework.throttling.ScopedRateThrottle',

    ],

    'DEFAULT_THROTTLE_RATES': {

        'anon': '30/min',

        'user': '120/min',

        'login': '5/min',

        'register': '10/hour',

    },

}


SIMPLE_JWT = {

    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    'ROTATE_REFRESH_TOKENS': False,

    'BLACKLIST_AFTER_ROTATION': True,

    'AUTH_HEADER_TYPES': ('Bearer',),

}


CORS_ALLOWED_ORIGINS = env.list(

    'CORS_ALLOWED_ORIGINS',

    default=['http://localhost:3000', 'http://127.0.0.1:3000'],

)


if DEBUG:

    CORS_ALLOW_ALL_ORIGINS = True


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

WHITENOISE_MAX_AGE = 31536000

if not DEBUG:

    STORAGES = {

        'default': {

            'BACKEND': 'django.core.files.storage.FileSystemStorage',

        },

        'staticfiles': {

            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',

        },

    }


MEDIA_ROOT = BASE_DIR / 'media'


MAX_MATERIAL_UPLOAD_MB = 100

MAX_SUBMISSION_UPLOAD_MB = 50

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


SECURE_REDIRECT_EXEMPT = [r'^health$']


if not DEBUG:

    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = 31536000

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

    if RENDER_EXTERNAL_HOSTNAME:

        origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'

        if origin not in CSRF_TRUSTED_ORIGINS:

            CSRF_TRUSTED_ORIGINS.append(origin)


LOGGING = {

    'version': 1,

    'disable_existing_loggers': False,

    'formatters': {

        'simple': {'format': '{levelname} {asctime} {name} {message}', 'style': '{'},

    },

    'handlers': {

        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},

    },

    'root': {'handlers': ['console'], 'level': 'INFO'},

    'loggers': {

        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},

    },

}
