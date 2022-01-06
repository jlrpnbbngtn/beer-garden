gardenService.$inject = ['$http'];

/**
 * gardenService - Service for interacting with the garden API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the garden API.
 */
export default function gardenService($http) {
  const GardenService = {};

  GardenService.getGardens = function() {
    return $http.get('api/v1/gardens/');
  };

  GardenService.getGarden = function(name) {
    return $http.get('api/v1/gardens/' + encodeURIComponent(name));
  };

  GardenService.createGarden = function(garden) {
    return $http.post('api/v1/gardens', garden);
  };

  GardenService.updateGardenConfig = function(garden) {
    return $http.patch('api/v1/gardens/' + encodeURIComponent(garden.name), {
      operation: 'config',
      path: '',
      value: garden,
    });
  };

  GardenService.syncGardens = function() {
    return $http.patch('api/v1/gardens', {
      operation: 'sync',
      path: '',
      value: '',
    });
  };

  GardenService.syncGarden = function(name) {
    return $http.patch('api/v1/gardens/' + encodeURIComponent(name), {
      operation: 'sync',
      path: '',
      value: '',
    });
  };

  GardenService.deleteGarden = function(name) {
    return $http.delete('api/v1/gardens/' + encodeURIComponent(name));
  };

  GardenService.serverModelToForm = function(model) {
    const values = {};
    const stompHeaders = [];
    values['connection_type'] = model['connection_type'];
    if (
      model.hasOwnProperty('connection_params') &&
      model.connection_params != null
    ) {
      for (const parameter of Object.keys(model['connection_params'])) {
        if (parameter == 'stomp_headers') {
          // eslint-disable-next-line guard-for-in
          for (const key in model['connection_params']['stomp_headers']) {
            stompHeaders[stompHeaders.length] = {
              key: key,
              value: model['connection_params']['stomp_headers'][key],
            };
          }
          values['stomp_headers'] = stompHeaders;
        } else {
          // Recursively remove null/empty values from json payload
          const parameterValue = (function filter(obj) {
            Object.entries(obj).forEach(
                ([key, val]) =>
                  (val && typeof val === 'object' && filter(val)) ||
                ((val === null || val === '') && delete obj[key]),
            );
            return obj;
          })(model.connection_params[parameter]);

          values[parameter] = parameterValue;
        }
      }
    }
    return values;
  };

  const isEmptyConnection = (entryPointName, entryPointValues) => {
    const simpleFieldMissing = (entry) => {
      // it's better to be explicit because of the inherent stupidity of
      // Javascript "truthiness"
      return typeof entryPointValues[entry] === 'undefined' ||
            entryPointValues[entry] === null ||
            entryPointValues[entry] === '';
    };

    if (entryPointName === 'stomp') {
      const stompSimpleFields = [
        'host', 'password', 'port', 'send_destination', 'subscribe_destination',
        'username',
      ];
      const stompSslFields = ['ca_cert', 'client_cert', 'client_key'];
      let nestedFieldsMissing = true;

      const allSimpleFieldsMissing = stompSimpleFields.every(simpleFieldMissing);

      const sslIsMissing = typeof entryPointValues['ssl'] === 'undefined' ||
        entryPointValues['ssl'] === {};

      if (!sslIsMissing) {
        nestedFieldsMissing = stompSslFields.every(
            (entry) =>
              typeof entryPointValues['ssl'][entry] == 'undefined' ||
            entryPointValues['ssl'][entry] == null ||
            entryPointValues['ssl'][entry] === '',
        );
      }

      return entryPointValues['headers'].length === 0 &&
        allSimpleFieldsMissing &&
        nestedFieldsMissing;
    }

    // is 'http'
    const httpSimpleFields = [
      'ca_cert', 'client_cert', 'host', 'port', 'url_prefix',
    ];

    return httpSimpleFields.every(simpleFieldMissing);
  };

  GardenService.formToServerModel = function(model, form) {
    /* Carefully pick apart the form data and translate it to the correct server
     * model. Throw an error if the entire form is empty (i.e., cannot have
     * empty connection parameters for both entry points).
     */
    const {connection_type: formConnectionType, ...formWithoutConxType} = form;
    model['connection_type'] = formConnectionType;

    const modelUpdatedConnectionParams = {};
    const emptyConnections = {};

    for (const formEntryPointName of Object.keys(formWithoutConxType)) {
      // formEntryPointName is either 'http' or 'stomp'
      const formEntryPointMap = formWithoutConxType[formEntryPointName];
      const modelUpdatedEntryPoint = {};

      for (const formEntryPointKey of Object.keys(formEntryPointMap)) {
        const formEntryPointValue = formEntryPointMap[formEntryPointKey];

        if (formEntryPointName === 'stomp' && formEntryPointKey === 'headers') {
          // the ugly corner case is the stomp headers
          const formStompHeaders = formEntryPointValue;
          const modelUpdatedStompHeaderArray = [];

          for (const formStompHeader of formStompHeaders) {
            const formStompKey = formStompHeader['key'];
            const formStompValue = formStompHeader['value'];

            // assume that we have both a key and a value or neither
            if (formStompKey && formStompValue) {
              modelUpdatedStompHeaderArray.push(
                  {
                    'key': formStompKey,
                    'value': formStompValue,
                  },
              );
            }
          }

          modelUpdatedEntryPoint['headers'] = modelUpdatedStompHeaderArray;
        } else {
          modelUpdatedEntryPoint[formEntryPointKey] = formEntryPointValue;
        }
      }
      if (!isEmptyConnection(formEntryPointName, modelUpdatedEntryPoint)) {
        modelUpdatedConnectionParams[formEntryPointName] =
          modelUpdatedEntryPoint;
      } else {
        emptyConnections[formEntryPointName] = true;
      }
    }

    if (emptyConnections['http'] && emptyConnections['stomp']) {
      throw Error('One of \'http\' or \'stomp\' connection must be defined');
    }

    model = {...model, 'connection_params': modelUpdatedConnectionParams};

    return model;
  };

  GardenService.CONNECTION_TYPES = ['HTTP', 'STOMP'];

  GardenService.SCHEMA = {
    type: 'object',
    required: ['connection_type'],
    properties: {
      connection_type: {
        title: 'Connection Type',
        description:
          'The type of connection that is established for the Garden to ' +
          'receive requests and events',
        type: 'string',
        enum: GardenService.CONNECTION_TYPES,
      },
      http: {
        title: ' ',
        type: 'object',
        properties: {
          name: {
            title: 'Garden Name',
            description:
              'This is the globally routing name that Beer Garden utilizes ' +
              'when routing requests and events',
            type: 'string',
          },
          host: {
            title: 'Host Name',
            description: 'Beer-garden hostname',
            type: 'string',
            minLength: 1,
          },
          port: {
            title: 'Port',
            description: 'Beer-garden port',
            type: 'integer',
            minLength: 1,
          },
          url_prefix: {
            title: 'URL Prefix',
            description:
              'URL path that will be used as a prefix when communicating ' +
              'with Beer-garden. Useful if Beer-garden is running on a URL ' +
              'other than \'/\'.',
            type: 'string',
          },
          ca_cert: {
            title: 'CA Cert Path',
            description:
              'Path to certificate file containing the certificate of the ' +
              'authority that issued the Beer-garden server certificate',
            type: 'string',
          },
          ca_verify: {
            title: 'CA Cert Verify',
            description: 'Whether to verify Beer-garden server certificate',
            type: 'boolean',
          },
          ssl: {
            title: 'SSL Enabled',
            description: 'Whether to connect with provided certifications',
            type: 'boolean',
          },
          client_cert: {
            title: 'Client Cert Path',
            description:
              'Path to client certificate to use when communicating with ' +
              'Beer-garden',
            type: 'string',
          },
        },
      },
      stomp: {
        title: ' ',
        type: 'object',
        properties: {
          host: {
            title: 'Host Name',
            description: 'Beer-garden hostname',
            type: 'string',
            minLength: 1,
          },
          port: {
            title: 'Port',
            description: 'Beer-garden port',
            type: 'integer',
            minLength: 1,
          },
          send_destination: {
            title: 'Send Destination',
            description: 'Destination queue where Stomp will send messages.',
            type: 'string',
          },
          subscribe_destination: {
            title: 'Subscribe Destination',
            description:
              'Destination queue where Stomp will listen for messages.',
            type: 'string',
          },
          username: {
            title: 'Username',
            description: 'Username for Stomp connection.',
            type: 'string',
          },
          password: {
            title: 'Password',
            description: 'Password for Stomp connection.',
            type: 'string',
          },
          ssl: {
            title: ' ',
            type: 'object',
            properties: {
              use_ssl: {
                title: 'SSL Enabled',
                description: 'Whether to connect with provided certifications',
                type: 'boolean',
              },
              ca_cert: {
                title: 'CA Cert',
                description:
                  'Path to certificate file containing the certificate of ' +
                  'the authority that issued the message broker certificate',
                type: 'string',
              },
              client_cert: {
                title: 'Client Cert',
                description:
                  'Path to client public certificate to use when ' +
                  'communicating with the message broker',
                type: 'string',
              },
              client_key: {
                title: 'Client Key',
                description:
                  'Path to client private key to use when communicating with ' +
                  'the message broker',
                type: 'string',
              },
            },
          },
          headers: {
            title: ' ',
            type: 'array',
            items: {
              title: ' ',
              type: 'object',
              properties: {
                key: {
                  title: 'Key',
                  description: '',
                  type: 'string',
                },
                value: {
                  title: 'Value',
                  description: '',
                  type: 'string',
                },
              },
            },
          },
        },
      },
    },
  };

  GardenService.FORM = [
    {
      type: 'fieldset',
      items: ['connection_type'],
    },
    {
      type: 'fieldset',
      items: [
        {
          type: 'tabs',
          tabs: [
            {
              title: 'HTTP',
              items: [
                'http.host',
                'http.port',
                'http.url_prefix',
                'http.ssl',
                'http.ca_cert',
                'http.ca_verify',
                'http.client_cert',
              ],
            },
            {
              title: 'STOMP',
              items: [
                'stomp.host',
                'stomp.port',
                'stomp.send_destination',
                'stomp.subscribe_destination',
                'stomp.username',
                'stomp.password',
                'stomp.ssl',
                {
                  'type': 'help',
                  'helpvalue': '<h4>Headers</h4><p>(Refresh browser if keys ' +
                  'and values are known to exist but are not populated on this' +
                  ' form)</p>',
                },
                'stomp.headers',
              ],
            },
          ],
        },
      ],
    },
    {
      type: 'section',
      htmlClass: 'row',
      items: [
        {
          type: 'submit',
          style: 'btn-primary w-100',
          title: 'Save Configuration',
          htmlClass: 'col-md-10',
        },
      ],
    },
  ];

  return GardenService;
}
