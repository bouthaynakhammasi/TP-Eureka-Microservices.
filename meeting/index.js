const express = require('express');
const { Eureka } = require('eureka-js-client');

const app = express();
const PORT = Number(process.env.PORT) || 8083;

// Configuration Eureka
const client = new Eureka({
  instance: {
    app: 'MEETING',
    // instanceId unique par port : sinon les instances s'écrasent dans le registre
    instanceId: `localhost:meeting:${PORT}`,
    hostName: 'localhost',
    ipAddr: '127.0.0.1',
    statusPageUrl: `http://localhost:${PORT}/health`,
    healthCheckUrl: `http://localhost:${PORT}/health`,
    homePageUrl: `http://localhost:${PORT}/`,
    port: {
      '$': PORT,
      '@enabled': true,
    },
    vipAddress: 'MEETING',
    dataCenterInfo: {
      '@class': 'com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo',
      name: 'MyOwn'
    },
  },
  eureka: {
    host: 'localhost',
    port: 8761,
    servicePath: '/eureka/apps/'
  }
});

// Démarrer le client Eureka
client.start((error) => {
  console.log(error || `Eureka registration complete - MEETING registered on port ${PORT}`);
});

// Endpoint hello
app.get('/api/meetings/hello', (req, res) => {
  res.json({ message: 'Hello from Meeting microservice!' });
});

// Endpoint health déclaré à Eureka (healthCheckUrl / statusPageUrl)
app.get('/health', (req, res) => {
  res.json({ service: 'MEETING', status: 'UP', port: PORT });
});

// Découverte de CANDIDAT via Eureka (aucune URL écrite en dur)
app.get('/api/meetings/candidat/:id', async (req, res) => {
  const instances = client.getInstancesByAppId('CANDIDAT')
    .filter((instance) => instance.status === 'UP');
  if (instances.length === 0) {
    return res.status(503).json({ error: 'Aucune instance CANDIDAT disponible dans Eureka' });
  }

  // Choix aléatoire d'une instance : répartition simple de la charge
  const instance = instances[Math.floor(Math.random() * instances.length)];
  const url = `http://${instance.hostName}:${instance.port.$}/api/candidates/${encodeURIComponent(req.params.id)}`;

  try {
    const response = await fetch(url);
    const body = await response.text();
    res.status(response.status)
      .set('X-Candidat-Instance', `${instance.hostName}:${instance.port.$}`)
      .type(response.headers.get('content-type') || 'application/json')
      .send(body);
  } catch (error) {
    res.status(502).json({ error: `Appel à CANDIDAT impossible (${url})`, details: error.message });
  }
});

// Démarrer le serveur
app.listen(PORT, () => {
  console.log(`Meeting microservice running on port ${PORT}`);
});

// Désenregistrement propre à l'arrêt
process.on('SIGINT', () => {
  console.log('Stopping Meeting microservice...');
  client.stop((error) => {
    console.log(error || 'Eureka unregistration complete');
    process.exit(0);
  });
});
