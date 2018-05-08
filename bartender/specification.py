SPECIFICATION = {
    "config": {
        "type": "str",
        "description": "Path to configuration file to use",
        "required": False,
        "cli_short_name": "c",
        "bootstrap": True,
    },
    "publish_hostname": {
        "type": "str",
        "default": "localhost",
        "description": "Publicly accessible hostname for plugins to connect to",
        "previous_names": ["amq_publish_host"],
    },
    'amq': {
        'type': 'dict',
        'items': {
            "host": {
                "type": "str",
                "default": "localhost",
                "description": "Hostname of AMQ to use",
                "previous_names": ["amq_host"],
            },
            "heartbeat_interval": {
                "type": "int",
                "default": 3600,
                "description": "Heartbeat interval for AMQ",
                "previous_names": ["amq_heartbeat_interval"],
            },
            "connection_attempts": {
                "type": "int",
                "default": 3,
                "description": "Number of retries to connect to AMQ",
                "previous_names": ["amq_connection_attempts"],
            },
            "exchange": {
                "type": "str",
                "default": "beer_garden",
                "description": "Exchange name to use for AMQ",
                "previous_names": ["amq_exchange"],
            },
            "virtual_host": {
                "type": "str",
                "default": "/",
                "description": "Virtual host to use for AMQ",
                "previous_names": ["amq_virtual_host"],
            },
            'connections': {
                'type': 'dict',
                'items': {
                    'admin': {
                        'type': 'dict',
                        'items': {
                            "port": {
                                "type": "int",
                                "default": 15672,
                                "description": "Port of the AMQ Admin host",
                                "previous_names": ["amq_admin_port"],
                            },
                            "user": {
                                "type": "str",
                                "default": "guest",
                                "description": "Username to login to the AMQ admin",
                                "previous_names": ["amq_admin_user"],
                            },
                            "password": {
                                "type": "str",
                                "default": "guest",
                                "description": "Password to login to the AMQ admin",
                                "previous_names": ["amq_admin_pw"],
                            },
                        },
                    },
                    'message': {
                        'type': 'dict',
                        'items': {
                            "port": {
                                "type": "int",
                                "default": 5672,
                                "description": "Port of the AMQ host",
                                "previous_names": ["amq_port"],
                            },
                            "password": {
                                "type": "str",
                                "default": "guest",
                                "description": "Password to login to the AMQ host",
                                "previous_names": ["amq_pw"],
                            },
                            "user": {
                                "type": "str",
                                "default": "guest",
                                "description": "Username to login to the AMQ host",
                                "previous_names": ["amq_user"],
                            },
                        },
                    },
                },
            },
        },
    },

    'db': {
        'type': 'dict',
        'items': {
            "name": {
                "type": "str",
                "default": "beer_garden",
                "description": "Name of the database to use",
                "previous_names": ["db_name"],
            },
            'connection': {
                'type': 'dict',
                'items': {
                    "host": {
                        "type": "str",
                        "default": "localhost",
                        "description": "Hostname/IP of the database server",
                        "previous_names": ["db_host"],
                    },
                    "password": {
                        "type": "str",
                        "default": None,
                        "required": False,
                        "description": "Password to connect to the database",
                        "previous_names": ["db_password"],
                    },
                    "port": {
                        "type": "int",
                        "default": 27017,
                        "description": "Port of the database server",
                        "previous_names": ["db_port"],
                    },
                    "username": {
                        "type": "str",
                        "default": None,
                        "required": False,
                        "description": "Username to connect to the database",
                        "previous_names": ["db_username"],
                    },
                },
            },
            'ttl': {
                'type': 'dict',
                'items': {
                    "event": {
                        "type": "int",
                        "default": 15,
                        "description": "Number of minutes to wait before deleting "
                                       "events (negative number for never)",
                        "previous_names": ["event_mongo_ttl"],
                    },
                    "action": {
                        "type": "int",
                        "default": -1,
                        "description": "Number of minutes to wait before deleting "
                                       "ACTION requests (negative number for never)",
                        "previous_names": ["action_request_ttl"],
                    },
                    "info": {
                        "type": "int",
                        "default": 15,
                        "description": "Number of minutes to wait before deleting INFO request",
                        "previous_names": ["info_request_ttl"],
                    },
                },
            },
        },
    },

    'log': {
        'type': 'dict',
        'items': {
            "config_file": {
                "type": "str",
                "description": "Path to a logging config file.",
                "required": False,
                "cli_short_name": "l",
                "previous_names": ["log_config"],
            },
            "file": {
                "type": "str",
                "description": "File you would like the application to log to",
                "required": False,
                "previous_names": ["log_file"],
            },
            "level": {
                "type": "str",
                "description": "Log level for the application",
                "default": "INFO",
                "choices": ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL"],
                "previous_names": ["log_level"],
            },
        },
    },

    'web': {
        'type': 'dict',
        'items': {
            "ca_cert": {
                "type": "str",
                "description": "Path to CA certificate file to use",
                "required": False,
                "previous_names": ["ca_cert"],
            },
            "ca_verify": {
                "type": "bool",
                "default": True,
                "description": "Verify external certificates",
                "required": False,
                "previous_names": ["ca_verify"],
            },
            "host": {
                "type": "str",
                "default": "localhost",
                "description": "Hostname of the API server",
                "previous_names": ["web_host"],
            },
            "port": {
                "type": "int",
                "default": 2337,
                "description": "Port of the API server",
                "previous_names": ["web_port"],
            },
            "ssl_enabled": {
                "type": "bool",
                "default": False,
                "description": "Is the API server using SSL",
                "previous_names": ["ssl_enabled"],
                "cli_separator": "_",
            },
            "url_prefix": {
                "type": "str",
                "default": None,
                "description": "URL prefix of the API server",
                "required": False,
                "previous_names": ["url_prefix"],
            },
        },
    },

    'thrift': {
        'type': 'dict',
        'items': {
            "max_workers": {
                "type": "int",
                "default": 25,
                "description": "Maximum number of threads for handling incoming thrift calls",
                "previous_names": ["max_thrift_workers"],
            },
            "host": {
                "type": "str",
                "default": "0.0.0.0",
                "description": "Host to bind the thrift server to",
                "previous_names": ["thrift_host"],
            },
            "port": {
                "type": "int",
                "default": 9090,
                "description": "Port to bind the thrift server to",
                "previous_names": ["thrift_port"],
            },
        },
    },

    'plugin': {
        'type': 'dict',
        'items': {
            "status_heartbeat": {
                "type": "int",
                "default": 10,
                "description": "Amount of time between status messages",
                "previous_names": ["plugin_status_heartbeat"],
            },
            "status_timeout": {
                "type": "int",
                "default": 30,
                "description": "Amount of time to wait before marking a plugin as unresponsive",
                "previous_names": ["plugin_status_timeout "],
            },
            'local': {
                'type': 'dict',
                'items': {
                    "directory": {
                        "type": "str",
                        "description": "Directory where local plugins are located",
                        "required": False,
                        "previous_names": ["plugins_directory", "plugin_directory"],
                    },
                    "log_directory": {
                        "type": "str",
                        "description": "Directory where local plugin logs should go",
                        "required": False,
                        "previous_names": ["plugin_log_directory"],
                    },
                    'timeout': {
                        'type': 'dict',
                        'items': {
                            "shutdown": {
                                "type": "int",
                                "default": 10,
                                "description": "Seconds to wait for a plugin to stop gracefully",
                                "previous_names": ["plugin_shutdown_timeout"],
                            },
                            "startup": {
                                "type": "int",
                                "default": 5,
                                "description": "Seconds to wait for a plugin to start",
                                "previous_names": ["plugin_startup_timeout"],
                            },
                        },
                    },
                },
            },
        },
    },
}


def get_default_logging_config(level, filename):
    if filename:
        bartender_handler = {
                "class": "logging.handlers.RotatingFileHandler",
                "level": level,
                "formatter": "simple",
                "filename": filename,
                "maxBytes": 10485760,
                "backupCount": 20,
                "encoding": "utf8"
        }
    else:
        bartender_handler = {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": level,
            "stream": "ext://sys.stdout"
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "bartender": bartender_handler
        },
        "loggers": {
            "pika": {
                "level": "ERROR"
            },
            "requests.packages.urllib3.connectionpool": {
                "level": "WARN"
            }
        },
        "root": {
            "level": level,
            "handlers": ["bartender"]
        }
    }
