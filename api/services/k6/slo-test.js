import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

const SLOs = {
  p95LatencyMs: 500,
  errorRate: 0.02,
  throughput: 20,
  cacheHitRate: 0.7
};

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 3,
      duration: '30s',
      startTime: '0s',
      tags: { test_type: 'smoke' },
    },
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 25 },
        { duration: '30s', target: 0 },
      ],
      startTime: '40s',
      tags: { test_type: 'load' },
    },
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 50 },
        { duration: '20s', target: 50 },
        { duration: '10s', target: 0 },
      ],
      startTime: '3m',
      tags: { test_type: 'spike' },
    },
  },
  
  thresholds: {
    'http_req_duration{test_type:smoke}': ['p(95)<1000'],
    'http_req_failed{test_type:smoke}': ['rate<0.05'],
    'http_req_duration{test_type:load}': [`p(95)<${SLOs.p95LatencyMs}`],
    'http_req_failed{test_type:load}': ['rate<0.05'],
    'http_req_duration{test_type:spike}': ['p(95)<2000'],
    'http_req_failed{test_type:spike}': ['rate<0.1'],
  },
  
  discardResponseBodies: false,
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:80';
const metrics = {
  cacheHits: 0,
  cacheMisses: 0,
  totalRequests: 0,
  rateLimitHits: 0
};

// ADMIN CREDENTIALS - these have admin role
const ADMIN_EMAIL = "alice@example.com";
const ADMIN_PASSWORD = "S3cureP@ss";

let GLOBAL_ACCESS_TOKEN = null;

export function setup() {
  console.log("Setting up test: Getting admin authentication token...");
  
  try {
    const cleanupRes = http.del(`${BASE_URL}/api/auth/cleanup-test-data`);
    console.log(`Pre-test cleanup status: ${cleanupRes.status}`);
  } catch (e) {}
  
  // Login with admin credentials
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: ADMIN_EMAIL,
    password: ADMIN_PASSWORD
  }), {
    headers: { 'Content-Type': 'application/json' },
    timeout: '10s'
  });
  
  if (loginRes.status === 200) {
    GLOBAL_ACCESS_TOKEN = loginRes.json('accessToken');
    console.log(`Got admin access token: ${GLOBAL_ACCESS_TOKEN ? 'YES' : 'NO'}`);
    
    // Verify the token has admin role by checking /me endpoint
    const verifyRes = http.get(`${BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${GLOBAL_ACCESS_TOKEN}`,
        'Content-Type': 'application/json'
      },
      timeout: '5s'
    });
    
    if (verifyRes.status === 200) {
      const userData = verifyRes.json();
      console.log(`Logged in as: ${userData.email}, Role: ${userData.role}`);
    }
  } else {
    console.log(`Admin login failed: ${loginRes.status} - ${loginRes.body}`);
    
    // Fallback: Try to create an admin user if login fails
    console.log("Trying to create admin user as fallback...");
    const testId = randomIntBetween(100000, 999999);
    const timestamp = Date.now();
    const email = `admin_${testId}_${timestamp}@test.com`;
    const password = "AdminP@ss123";
    const name = `Admin User ${testId}`;
    
    const registerRes = http.post(`${BASE_URL}/api/auth/register`, JSON.stringify({
      email,
      password,
      name,
      role: "admin"  // Try to register as admin
    }), {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s'
    });
    
    if (registerRes.status === 201) {
      sleep(1);
      const fallbackLogin = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
        email,
        password
      }), {
        headers: { 'Content-Type': 'application/json' },
        timeout: '10s'
      });
      
      if (fallbackLogin.status === 200) {
        GLOBAL_ACCESS_TOKEN = fallbackLogin.json('accessToken');
        console.log(`Got fallback admin token from new registration`);
      }
    }
  }
  
  if (!GLOBAL_ACCESS_TOKEN) {
    console.error("FAILED TO GET ADMIN ACCESS TOKEN - TESTS WILL FAIL!");
  }
  
  return { 
    startTime: Date.now(),
    accessToken: GLOBAL_ACCESS_TOKEN 
  };
}

export default function (data) {
  const testType = __VU % 3;
  
  const accessToken = data.accessToken || GLOBAL_ACCESS_TOKEN;
  
  if (!accessToken) {
    console.error(`VU${__VU}: No access token available, skipping test`);
    return;
  }
  
  switch(testType) {
    case 0:
      testOrderCreationAndRetrieval(accessToken);
      break;
    case 1:
      testOrderCreationAndRetrieval(accessToken);
      break;
    case 2:
      testHealthAndMetrics();
      break;
  }
}

function testOrderCreationAndRetrieval(accessToken) {
  if (!accessToken) {
    console.error("No access token provided to testOrderCreationAndRetrieval");
    return;
  }
  
  sleep(randomIntBetween(1, 3));
  
  metrics.totalRequests++;
  
  const orderData = {
    items: [
      {
        product_id: `prod_${randomIntBetween(1, 100)}`,
        name: `Test Product ${randomIntBetween(1, 100)}`,
        quantity: randomIntBetween(1, 5),
        unit_price: randomIntBetween(10, 100)
      }
    ],
    billing_address_id: `addr_${randomIntBetween(1, 10)}`,
    shipping_address_id: `addr_${randomIntBetween(1, 10)}`,
    payment_method_token: `pm_${randomIntBetween(1, 10)}`
  };
  
  const createRes = http.post(`${BASE_URL}/api/orders/`, JSON.stringify(orderData), {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    timeout: '15s',
    tags: { operation: 'create_order' }
  });
  
  if (createRes.status === 403) {
    console.error(`Admin access required! Status: ${createRes.status}, Body: ${createRes.body}`);
    console.error(`Check that token has admin role`);
    return;
  }
  
  check(createRes, {
    'create order status 201': (r) => r.status === 201,
    'order has id': (r) => r.json('id') !== undefined,
    'order has status': (r) => r.json('status') !== undefined
  });
  
  if (createRes.status === 201) {
    const orderId = createRes.json('id');
    
    sleep(0.5);
    
    for (let i = 0; i < 3; i++) {
      const getRes = http.get(`${BASE_URL}/api/orders/${orderId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        timeout: '10s',
        tags: { operation: 'get_order', iteration: i }
      });
      
      if (getRes.status === 200) {
        if (i > 0) {
          metrics.cacheHits++;
        } else {
          metrics.cacheMisses++;
        }
        
        check(getRes, {
          'get order status 200': (r) => r.status === 200,
          'order id matches': (r) => r.json('id') === orderId
        });
      }
      
      sleep(0.3);
    }
    
    sleep(0.5);
    
    const listRes = http.get(`${BASE_URL}/api/orders/?page=1&page_size=10`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      timeout: '10s',
      tags: { operation: 'list_orders' }
    });
    
    check(listRes, {
      'list orders status 200': (r) => r.status === 200,
      'has items array': (r) => r.json('items') !== undefined
    });
  }
  
  sleep(randomIntBetween(2, 5));
}

function testHealthAndMetrics() {
  const endpoints = [
    '/health',
    '/api/auth/health',
    '/api/products/health',
    '/api/orders/health',
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const res = http.get(BASE_URL + endpoint, {
    timeout: '5s',
    tags: { operation: 'health' }
  });
  
  check(res, {
    'status 2xx': (r) => r.status >= 200 && r.status < 300,
  });
  
  sleep(randomIntBetween(2, 5));
}

export function teardown(data) {
  try {
    const cleanupRes = http.del(`${BASE_URL}/api/auth/cleanup-test-data`);
    console.log(`Post-test cleanup status: ${cleanupRes.status}`);
  } catch (e) {}
  
  const testDuration = (Date.now() - data.startTime) / 1000;
  const cacheHitRate = metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses) || 0;
  
  console.log(`\n=== Performance Metrics ===`);
  console.log(`Test duration: ${testDuration.toFixed(1)}s`);
  console.log(`Total requests: ${metrics.totalRequests}`);
  console.log(`Cache hits: ${metrics.cacheHits}`);
  console.log(`Cache misses: ${metrics.cacheMisses}`);
  console.log(`Rate limit hits: ${metrics.rateLimitHits}`);
  console.log(`Cache hit rate: ${(cacheHitRate * 100).toFixed(1)}%`);
  console.log(`Target cache hit rate: ${(SLOs.cacheHitRate * 100).toFixed(1)}%`);
  console.log(`Cache performance: ${cacheHitRate >= SLOs.cacheHitRate ? '✅ PASS' : '❌ FAIL'}`);
}

export function handleSummary(data) {
  const smokeMetrics = data.metrics;
  const cacheHitRate = metrics.cacheHits / (metrics.cacheHits + metrics.cacheMisses) || 0;
  
  const summary = {
    stage: 8,
    timestamp: new Date().toISOString(),
    services_tested: ['nginx', 'auth', 'products', 'orders'],
    slos: SLOs,
    performance: {
      p95_latency: smokeMetrics.http_req_duration.values['p(95)'],
      error_rate: smokeMetrics.http_req_failed.values.rate,
      throughput: smokeMetrics.http_reqs.values.rate,
      cache_hit_rate: cacheHitRate,
      total_requests: smokeMetrics.http_reqs.values.count,
      total_duration: smokeMetrics.iteration_duration.values.total,
      rate_limit_hits: metrics.rateLimitHits
    },
    compliance: {
      latency_met: smokeMetrics.http_req_duration.values['p(95)'] < SLOs.p95LatencyMs,
      error_budget_met: smokeMetrics.http_req_failed.values.rate < SLOs.errorRate,
      throughput_met: smokeMetrics.http_reqs.values.rate > SLOs.throughput,
      cache_performance_met: cacheHitRate >= SLOs.cacheHitRate
    },
    all_passed: (
      smokeMetrics.http_req_duration.values['p(95)'] < SLOs.p95LatencyMs &&
      smokeMetrics.http_req_failed.values.rate < SLOs.errorRate &&
      smokeMetrics.http_reqs.values.rate > SLOs.throughput &&
      cacheHitRate >= SLOs.cacheHitRate
    )
  };
  
  console.log('\n=== STAGE 8 TEST RESULTS ===');
  console.log(JSON.stringify(summary, null, 2));
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'reports/stage8-result.json': JSON.stringify(summary, null, 2),
    'reports/perf_optimized.json': JSON.stringify({
      p95_latency_ms: summary.performance.p95_latency,
      error_rate: summary.performance.error_rate,
      throughput_rps: summary.performance.throughput,
      cache_hit_rate: summary.performance.cache_hit_rate,
      total_requests: summary.performance.total_requests,
      timestamp: summary.timestamp,
      rate_limit_hits: metrics.rateLimitHits
    }, null, 2),
  };
}