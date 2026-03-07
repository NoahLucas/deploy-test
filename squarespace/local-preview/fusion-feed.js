(function () {
  var fallback = {
    headline: 'Current operating signal: high creative throughput with room to reduce context switching.',
    metrics: {
      recovery: '84/100',
      focus: '91/100',
      balance: '76/100',
      action: 'Protect two 90-minute deep-work windows before noon.'
    }
  };

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) {
      el.textContent = value;
    }
  }

  function apply(data) {
    setText('fusion-headline', data.headline);
    setText('fusion-recovery', data.metrics.recovery);
    setText('fusion-focus', data.metrics.focus);
    setText('fusion-balance', data.metrics.balance);
    setText('fusion-action', data.metrics.action);
  }

  fetch('http://127.0.0.1:8000/api/v1/public/feed', {
    headers: { Accept: 'application/json' }
  })
    .then(function (res) {
      if (!res.ok) {
        throw new Error('unavailable');
      }
      return res.json();
    })
    .then(function (data) {
      apply({
        headline: data.headline,
        metrics: {
          recovery: data.metrics.recovery,
          focus: data.metrics.focus,
          balance: data.metrics.balance,
          action: data.metrics.action
        }
      });
    })
    .catch(function () {
      apply(fallback);
    });
})();
