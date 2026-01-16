/**
 * Artillery processor for Windows-AI load testing
 * Provides custom functions for complex scenarios and data generation
 */

// Generate random user ID
function generateUserId(context, ee, next) {
  context.vars.userId = `user_${Math.random().toString(36).substr(2, 9)}`;
  return next();
}

// Generate random plugin configuration
function generatePluginConfig(context, ee, next) {
  context.vars.pluginConfig = {
    enabled: Math.random() > 0.5,
    timeout: Math.floor(Math.random() * 10000) + 1000,
    retries: Math.floor(Math.random() * 5),
    cache_ttl: Math.floor(Math.random() * 3600),
  };
  return next();
}

// Log request details
function logRequest(context, ee, next) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] Request: ${context.vars.method || 'GET'} ${context.vars.url}`);
  return next();
}

// Process response
function processResponse(context, ee, next) {
  if (context.vars.response) {
    const responseTime = context.vars.response.elapsed || 0;
    context.vars.responseTime = responseTime;
    
    if (responseTime > 1000) {
      console.warn(`Slow response detected: ${responseTime}ms`);
    }
  }
  return next();
}

// Simulate think time based on response
function thinkBasedOnResponse(context, ee, next) {
  if (context.vars.response && context.vars.response.status === 503) {
    // Service unavailable - wait longer
    context.vars.thinkTime = Math.random() * 5000 + 5000; // 5-10 seconds
  } else if (context.vars.response && context.vars.response.elapsed > 500) {
    // Slow response - wait a bit
    context.vars.thinkTime = Math.random() * 2000 + 1000; // 1-3 seconds
  } else {
    // Normal response - wait normally
    context.vars.thinkTime = Math.random() * 1000 + 500; // 500ms-1.5s
  }
  return next();
}

// Extract plugin IDs from list response
function extractPluginIds(context, ee, next) {
  if (context.vars.plugins && Array.isArray(context.vars.plugins)) {
    context.vars.pluginIds = context.vars.plugins.map(p => p.id);
    if (context.vars.pluginIds.length > 0) {
      context.vars.randomPluginId = context.vars.pluginIds[
        Math.floor(Math.random() * context.vars.pluginIds.length)
      ];
    }
  }
  return next();
}

// Validate response structure
function validateResponse(context, ee, next) {
  const response = context.vars.response;
  if (response && response.statusCode === 200) {
    try {
      const body = response.body;
      if (typeof body === 'string') {
        JSON.parse(body);
      }
      context.vars.validResponse = true;
    } catch (e) {
      context.vars.validResponse = false;
      console.error(`Invalid JSON response: ${e.message}`);
    }
  }
  return next();
}

// Generate realistic API payloads
function generatePayload(context, ee, next) {
  const payloads = {
    webhook_event: {
      event: 'webhook.received',
      timestamp: new Date().toISOString(),
      data: {
        id: `evt_${Math.random().toString(36).substr(2, 9)}`,
        status: 'pending',
        metadata: {
          source: 'test',
          version: '1.0'
        }
      }
    },
    batch_operation: {
      operations: [
        {
          type: 'list',
          resource: 'plugins',
          filters: { active: true }
        },
        {
          type: 'execute',
          plugin: 'webhook_handler',
          action: 'trigger'
        },
        {
          type: 'query',
          resource: 'logs',
          filters: { level: 'error' }
        }
      ]
    },
    data_sync: {
      entities: [
        {
          id: `ent_${Math.random().toString(36).substr(2, 9)}`,
          type: 'plugin_config',
          data: {
            name: 'Performance Test Plugin',
            version: '1.0.0',
            enabled: true
          }
        }
      ],
      timestamp: new Date().toISOString()
    }
  };

  context.vars.payload = payloads.webhook_event; // Default
  return next();
}

// Measure request performance
function measurePerformance(context, ee, next) {
  context.vars.startTime = Date.now();
  return next();
}

function recordPerformance(context, ee, next) {
  const endTime = Date.now();
  const duration = endTime - context.vars.startTime;
  
  context.vars.performanceMetrics = {
    duration: duration,
    timestamp: new Date().toISOString(),
    endpoint: context.vars.endpoint,
    statusCode: context.vars.statusCode
  };

  // Categorize performance
  if (duration < 100) {
    context.vars.performanceCategory = 'excellent';
  } else if (duration < 500) {
    context.vars.performanceCategory = 'good';
  } else if (duration < 1000) {
    context.vars.performanceCategory = 'acceptable';
  } else if (duration < 5000) {
    context.vars.performanceCategory = 'slow';
  } else {
    context.vars.performanceCategory = 'critical';
  }

  return next();
}

// Handle rate limiting
function handleRateLimit(context, ee, next) {
  if (context.vars.statusCode === 429) {
    // Too many requests - exponential backoff
    const retryAfter = context.vars.retryAfter || Math.floor(Math.random() * 5) + 1;
    context.vars.backoffTime = retryAfter * 1000;
    console.warn(`Rate limited, backing off for ${retryAfter}s`);
  }
  return next();
}

// Aggregate metrics
let totalRequests = 0;
let totalDuration = 0;
let errorCount = 0;
let performanceDistribution = {
  excellent: 0,
  good: 0,
  acceptable: 0,
  slow: 0,
  critical: 0
};

function aggregateMetrics(context, ee, next) {
  totalRequests++;
  totalDuration += context.vars.performanceMetrics?.duration || 0;
  
  if (context.vars.statusCode >= 400) {
    errorCount++;
  }

  const category = context.vars.performanceCategory || 'unknown';
  if (performanceDistribution[category] !== undefined) {
    performanceDistribution[category]++;
  }

  // Log summary every 100 requests
  if (totalRequests % 100 === 0) {
    const avgDuration = totalDuration / totalRequests;
    const errorRate = (errorCount / totalRequests * 100).toFixed(2);
    console.log(`
    === Metrics Summary (${totalRequests} requests) ===
    Average Duration: ${avgDuration.toFixed(2)}ms
    Error Rate: ${errorRate}%
    Performance Distribution:
      - Excellent (<100ms): ${performanceDistribution.excellent}
      - Good (100-500ms): ${performanceDistribution.good}
      - Acceptable (500-1000ms): ${performanceDistribution.acceptable}
      - Slow (1000-5000ms): ${performanceDistribution.slow}
      - Critical (>5000ms): ${performanceDistribution.critical}
    `);
  }

  return next();
}

module.exports = {
  generateUserId: generateUserId,
  generatePluginConfig: generatePluginConfig,
  logRequest: logRequest,
  processResponse: processResponse,
  thinkBasedOnResponse: thinkBasedOnResponse,
  extractPluginIds: extractPluginIds,
  validateResponse: validateResponse,
  generatePayload: generatePayload,
  measurePerformance: measurePerformance,
  recordPerformance: recordPerformance,
  handleRateLimit: handleRateLimit,
  aggregateMetrics: aggregateMetrics,
};
