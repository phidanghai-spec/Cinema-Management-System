/* ============================================================
   CineVerse — Premium Client-Side JavaScript v2.0
   ============================================================ */

'use strict';

// ── 1. Toast Notification System ──────────────────────────────
window.showToast = function(title, message, type = 'info', duration = 4000) {
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            ${message ? `<div class="toast-msg">${message}</div>` : ''}
        </div>
        <button onclick="this.closest('.toast').remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:18px;padding:0 0 0 10px;line-height:1;align-self:flex-start;">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 350);
    }, duration);
};

// ── 2. Navbar Scroll Effect ────────────────────────────────────
(function() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });
})();

// ── 3. Hero Carousel ──────────────────────────────────────────
(function() {
    const track = document.getElementById('hero-track');
    if (!track) return;
    
    const slides = track.querySelectorAll('.hero-slide');
    const dots   = document.querySelectorAll('.hero-dot');
    if (slides.length < 2) return;
    
    let current  = 0;
    let interval;
    
    function goTo(idx) {
        current = (idx + slides.length) % slides.length;
        track.style.transform = `translateX(-${current * 100}%)`;
        dots.forEach((d, i) => d.classList.toggle('active', i === current));
    }
    
    function next() { goTo(current + 1); }
    
    function start() { interval = setInterval(next, 5500); }
    function stop()  { clearInterval(interval); }
    
    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => { stop(); goTo(i); start(); });
    });
    
    // Pause on hover
    const slider = document.querySelector('.hero-slider');
    if (slider) {
        slider.addEventListener('mouseenter', stop);
        slider.addEventListener('mouseleave', start);
    }
    
    // Touch support
    let touchX = 0;
    track.addEventListener('touchstart', e => { touchX = e.touches[0].clientX; stop(); }, { passive: true });
    track.addEventListener('touchend',   e => {
        const diff = touchX - e.changedTouches[0].clientX;
        if (Math.abs(diff) > 50) diff > 0 ? next() : goTo(current - 1);
        start();
    });
    
    goTo(0);
    start();
})();

// ── 4. Seat Selection ─────────────────────────────────────────
(function() {
    const seatsContainer = document.querySelector('.seat-grid');
    if (!seatsContainer) return;

    const multiplier    = parseFloat(document.getElementById('showtime-multiplier')?.value || '1.0');
    const showtimeId    = document.getElementById('booking-showtime-id')?.value;
    const checkoutBtn   = document.getElementById('booking-checkout-btn');
    const subtotalEl    = document.getElementById('booking-subtotal');
    const totalEl       = document.getElementById('booking-total');
    const seatListEl    = document.getElementById('selected-seats-list');
    const seatCountEl   = document.getElementById('seat-count-badge');
    
    let selectedSeats = [];
    let selectedCombos = [];
    let discountAmount = 0;
    let redeemedPoints = 0;

    function formatVND(n) { return n.toLocaleString('vi-VN'); }

    function updateSummary() {
        const subtotal = selectedSeats.reduce((sum, s) => sum + s.price, 0);
        const combosSubtotal = selectedCombos.reduce((sum, c) => sum + (c.price * c.quantity), 0);
        const pointsDiscount = redeemedPoints * 1000;
        const total    = Math.max(0, subtotal - discountAmount - pointsDiscount) + combosSubtotal;
        
        if (subtotalEl) subtotalEl.textContent = formatVND(subtotal);
        
        // Update combos subtotal in UI
        const combosSubtotalRow = document.getElementById('combos-subtotal-row');
        const combosSubtotalEl = document.getElementById('booking-combos-subtotal');
        if (combosSubtotalRow && combosSubtotalEl) {
            if (combosSubtotal > 0) {
                combosSubtotalEl.textContent = formatVND(combosSubtotal);
                combosSubtotalRow.style.display = 'flex';
            } else {
                combosSubtotalRow.style.display = 'none';
            }
        }
        
        // Update combos list in summary
        const summaryCombosRow = document.getElementById('summary-combos-row');
        const summaryCombosList = document.getElementById('summary-combos-list');
        if (summaryCombosRow && summaryCombosList) {
            if (selectedCombos.length > 0) {
                summaryCombosList.innerHTML = selectedCombos.map(c => 
                    `<div style="display:flex; justify-content:space-between; color:white;">
                        <span>${c.name} x${c.quantity}</span>
                        <span>${formatVND(c.price * c.quantity)} VNĐ</span>
                     </div>`
                ).join('');
                summaryCombosRow.style.display = 'flex';
            } else {
                summaryCombosRow.style.display = 'none';
            }
        }

        if (totalEl)    totalEl.textContent    = formatVND(total);
        if (seatListEl) seatListEl.textContent = selectedSeats.length
            ? selectedSeats.map(s => s.number).join(', ')
            : 'None';
        if (seatCountEl) seatCountEl.textContent = selectedSeats.length;
        
        // Show/hide points discount row
        const ptsDiscountRow = document.getElementById('points-discount-row');
        const ptsDiscountDisp = document.getElementById('points-discount-display');
        if (ptsDiscountRow && ptsDiscountDisp) {
            if (pointsDiscount > 0) {
                ptsDiscountDisp.textContent = formatVND(pointsDiscount);
                ptsDiscountRow.style.display = 'flex';
            } else {
                ptsDiscountRow.style.display = 'none';
            }
        }

        if (checkoutBtn) {
            checkoutBtn.disabled = selectedSeats.length === 0;
        }
        
        const hiddenInput = document.getElementById('selected-seat-ids-input');
        if (hiddenInput) hiddenInput.value = JSON.stringify(selectedSeats.map(s => s.id));
    }

    async function checkSuggestedDiscount() {
        const box = document.getElementById('suggested-promo-box');
        const codeEl = document.getElementById('suggested-promo-code');
        if (!box || !codeEl) return;
        
        if (selectedSeats.length === 0) {
            box.style.display = 'none';
            return;
        }
        
        const subtotal = selectedSeats.reduce((sum, s) => sum + s.price, 0);
        
        try {
            const res = await fetch('/api/discount/suggest/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({
                    subtotal,
                    showtime_id: parseInt(showtimeId),
                    seat_ids: selectedSeats.map(s => s.id),
                    redeemed_points: redeemedPoints
                })
            });
            const data = await res.json();
            if (data.success && data.suggested) {
                const currentCode = document.getElementById('applied-discount-code-input')?.value;
                if (currentCode !== data.code) {
                    codeEl.textContent = `${data.code} (-${formatVND(data.discount_amount)} VNĐ)`;
                    codeEl.dataset.code = data.code;
                    box.style.display = 'block';
                } else {
                    box.style.display = 'none';
                }
            } else {
                box.style.display = 'none';
            }
        } catch (err) {
            console.error("Error suggesting coupon:", err);
        }
    }

    seatsContainer.addEventListener('click', e => {
        const cell = e.target.closest('.seat-cell');
        if (!cell || cell.classList.contains('booked') || cell.classList.contains('maintenance')) return;
        
        const seatId     = parseInt(cell.dataset.seatId);
        const seatNumber = cell.dataset.number;
        const basePrice  = parseInt(cell.dataset.price);
        const price      = Math.round(basePrice * multiplier);
        
        const existingIdx = selectedSeats.findIndex(s => s.id === seatId);
        if (existingIdx >= 0) {
            selectedSeats.splice(existingIdx, 1);
            cell.classList.remove('selected');
        } else {
            selectedSeats.push({ id: seatId, number: seatNumber, price });
            cell.classList.add('selected');
        }
        updateSummary();
        checkSuggestedDiscount();
    });

    // Select combo quantities
    const comboSelectors = document.querySelectorAll('.quantity-selector');
    comboSelectors.forEach(container => {
        const comboId = parseInt(container.dataset.comboId);
        const comboName = container.dataset.comboName;
        const comboPrice = parseInt(container.dataset.comboPrice);
        const qtyEl = container.querySelector('.combo-qty');
        
        container.querySelector('.combo-minus-btn').addEventListener('click', () => {
            let qty = parseInt(qtyEl.textContent);
            if (qty > 0) {
                qty--;
                qtyEl.textContent = qty;
                updateComboQty(comboId, comboName, comboPrice, qty);
            }
        });
        
        container.querySelector('.combo-plus-btn').addEventListener('click', () => {
            let qty = parseInt(qtyEl.textContent);
            qty++;
            qtyEl.textContent = qty;
            updateComboQty(comboId, comboName, comboPrice, qty);
        });
    });

    function updateComboQty(id, name, price, qty) {
        const existingIdx = selectedCombos.findIndex(c => c.id === id);
        if (qty === 0) {
            if (existingIdx >= 0) selectedCombos.splice(existingIdx, 1);
        } else {
            if (existingIdx >= 0) {
                selectedCombos[existingIdx].quantity = qty;
            } else {
                selectedCombos.push({ id, name, price, quantity: qty });
            }
        }
        updateSummary();
    }

    // Promo Code
    const applyBtn = document.getElementById('apply-promo-btn');
    const promoMsg = document.getElementById('promo-message');
    const promoInput = document.getElementById('promo-code-input');
    const discountInput = document.getElementById('applied-discount-value');
    const discountCodeInput = document.getElementById('applied-discount-code-input');

    if (applyBtn) {
        applyBtn.addEventListener('click', async () => {
            const code = promoInput?.value.trim();
            if (!code) return;
            const subtotal = selectedSeats.reduce((sum, s) => sum + s.price, 0);
            if (subtotal === 0) {
                showToast('Chọn ghế trước', 'Vui lòng chọn ít nhất một ghế trước khi áp dụng voucher.', 'warning');
                return;
            }
            try {
                applyBtn.textContent = '...';
                const res  = await fetch('/api/discount/validate/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify({ code, subtotal })
                });
                const data = await res.json();
                if (data.success) {
                    discountAmount = data.discount_amount;
                    if (discountInput)    discountInput.value    = discountAmount;
                    if (discountCodeInput) discountCodeInput.value = data.code;
                    if (promoMsg) { promoMsg.style.color = 'var(--success)'; promoMsg.textContent = `✅ Áp dụng coupon thành công! Giảm ${formatVND(discountAmount)} VNĐ`; }
                    updateSummary();
                    showToast('Đã áp dụng Voucher!', `Bạn được giảm ${formatVND(discountAmount)} VNĐ từ mã ${data.code}`, 'success');
                    checkSuggestedDiscount();
                } else {
                    if (promoMsg) { promoMsg.style.color = 'var(--danger)'; promoMsg.textContent = `❌ ${data.error}`; }
                    discountAmount = 0;
                    showToast('Voucher không hợp lệ', data.error, 'error');
                }
            } catch {
                showToast('Lỗi mạng', 'Không thể xác thực voucher. Vui lòng thử lại.', 'error');
            } finally {
                applyBtn.textContent = 'Apply';
            }
        });
    }

    // Apply Suggested Code
    const applySuggestedBtn = document.getElementById('apply-suggested-btn');
    if (applySuggestedBtn) {
        applySuggestedBtn.addEventListener('click', () => {
            const codeEl = document.getElementById('suggested-promo-code');
            const code = codeEl?.dataset.code;
            if (code && promoInput) {
                promoInput.value = code;
                applyBtn.click();
            }
        });
    }

    // Points Redemption
    const applyPointsBtn = document.getElementById('apply-points-btn');
    const pointsInput = document.getElementById('redeem-points-input');
    const pointsMsg = document.getElementById('points-message');
    const appliedPointsVal = document.getElementById('applied-points-value');

    if (applyPointsBtn && pointsInput) {
        applyPointsBtn.addEventListener('click', () => {
            const pts = parseInt(pointsInput.value) || 0;
            const subtotal = selectedSeats.reduce((sum, s) => sum + s.price, 0);
            if (subtotal === 0) {
                showToast('Chọn ghế trước', 'Vui lòng chọn ghế trước khi đổi điểm.', 'warning');
                return;
            }
            if (pts < 0) {
                showToast('Lỗi', 'Số điểm không hợp lệ.', 'error');
                return;
            }
            const maxPoints = parseInt(pointsInput.getAttribute('max')) || 0;
            if (pts > maxPoints) {
                showToast('Lỗi', `Số điểm vượt quá số dư hiện tại (${maxPoints} điểm).`, 'error');
                return;
            }
            
            const pointValue = pts * 1000;
            if (pointValue > Math.floor(subtotal * 0.5)) {
                showToast('Giới hạn đổi điểm', 'Giá trị đổi điểm không được vượt quá 50% tiền vé.', 'warning');
                return;
            }
            
            redeemedPoints = pts;
            if (appliedPointsVal) appliedPointsVal.value = pts;
            
            if (pointsMsg) {
                if (pts > 0) {
                    pointsMsg.style.color = 'var(--success)';
                    pointsMsg.textContent = `✅ Đã áp dụng đổi ${pts} điểm (Giảm ${formatVND(pointValue)} VNĐ)`;
                } else {
                    pointsMsg.style.color = 'var(--text-muted)';
                    pointsMsg.textContent = '1 điểm = 1,000 VNĐ giảm giá (Tối đa 50% tiền vé)';
                }
            }
            
            updateSummary();
            showToast('Đã đổi điểm!', `Giảm ngay ${formatVND(pointValue)} VNĐ vào hóa đơn.`, 'success');
            checkSuggestedDiscount();
        });
    }

    // Payment Method Toggle
    const paymentCards = document.querySelectorAll('.payment-card');
    paymentCards.forEach(card => {
        card.addEventListener('click', () => {
            paymentCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            const radio = card.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
            
            const method = card.dataset.method;
            document.getElementById('credit-card-fields').style.display = method === 'credit_card' ? 'block' : 'none';
            document.getElementById('momo-fields').style.display = method === 'momo' ? 'block' : 'none';
        });
    });

    // Booking Step Navigation
    const stepBtns = document.querySelectorAll('[data-goto-step]');
    stepBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = parseInt(btn.dataset.gotoStep);
            if (target === 2 && selectedSeats.length === 0) {
                showToast('No Seats Selected', 'Please select at least one seat to continue.', 'warning');
                return;
            }
            goToStep(target);
        });
    });

    function goToStep(n) {
        document.querySelectorAll('.booking-step-panel').forEach((p, i) => {
            p.style.display = (i + 1) === n ? 'block' : 'none';
        });
        document.querySelectorAll('.booking-step').forEach((s, i) => {
            s.classList.toggle('active', i + 1 === n);
            s.classList.toggle('done', i + 1 < n);
        });
        window.scrollTo({ top: 200, behavior: 'smooth' });
    }

    // Checkout Form Submit
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', async e => {
            e.preventDefault();
            if (selectedSeats.length === 0) {
                showToast('No Seats', 'Please select at least one seat.', 'warning');
                return;
            }
            const btn = document.getElementById('booking-checkout-btn');
            btn.disabled = true;
            btn.textContent = '⏳ Processing Payment...';
            
            const method = checkoutForm.querySelector('input[name="payment_method"]:checked')?.value || 'credit_card';
            const notes  = document.getElementById('booking-notes')?.value || '';
            const discCode = discountCodeInput?.value || '';
            
            try {
                const res  = await fetch('/api/booking/create/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                    body: JSON.stringify({
                        showtime_id: parseInt(showtimeId),
                        seat_ids: selectedSeats.map(s => s.id),
                        combo_items: selectedCombos.map(c => ({ combo_id: c.id, quantity: c.quantity })),
                        discount_code: discCode || null,
                        payment_method: method,
                        notes,
                        redeemed_points: redeemedPoints
                    })
                });
                const data = await res.json();
                if (data.success) {
                    if (data.redirect_url) {
                        showToast('Thanh toán qua MoMo... 🎉', 'Đang chuyển hướng sang cổng thanh toán...', 'success', 2000);
                        setTimeout(() => { window.location.href = data.redirect_url; }, 1400);
                    } else {
                        showToast('Đặt vé thành công! 🎉', 'Đang tải vé của bạn...', 'success', 2000);
                        setTimeout(() => { window.location.href = `/booking/ticket/${data.booking_id}/`; }, 1400);
                    }
                } else {
                    showToast('Đặt vé thất bại', data.error, 'error');
                    btn.disabled = false;
                    btn.textContent = 'Complete Payment';
                }
            } catch {
                showToast('Lỗi mạng', 'Vui lòng kiểm tra kết nối mạng và thử lại.', 'error');
                btn.disabled = false;
                btn.textContent = 'Complete Payment';
            }
        });
    }
    
    updateSummary();
})();

// ── 5. QR Code Generation on Ticket Page ──────────────────────
(function() {
    const qrContent = document.getElementById('qr-content-value')?.value;
    const qrTarget  = document.getElementById('qr-render-target');
    if (!qrContent || !qrTarget) return;

    // Load qrcode.js from CDN
    if (typeof QRCode === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
        script.onload = () => renderQR();
        document.head.appendChild(script);
    } else {
        renderQR();
    }

    function renderQR() {
        qrTarget.innerHTML = '';
        new QRCode(qrTarget, {
            text: qrContent,
            width: 160,
            height: 160,
            colorDark: '#0f172a',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    }
})();

// ── 6. Print Ticket ────────────────────────────────────────────
(function() {
    const printBtn = document.getElementById('print-ticket-btn');
    if (printBtn) printBtn.addEventListener('click', () => window.print());
})();

// ── 7. Copy Booking Code ───────────────────────────────────────
(function() {
    const copyBtns = document.querySelectorAll('[data-copy]');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navigator.clipboard.writeText(btn.dataset.copy).then(() => {
                showToast('Copied!', btn.dataset.copy, 'success', 2000);
            });
        });
    });
})();

// ── 8. Profile Tabs ────────────────────────────────────────────
(function() {
    const tabs   = document.querySelectorAll('.profile-tab');
    const panels = document.querySelectorAll('.tab-panel');
    if (!tabs.length) return;
    
    // Check URL hash for initial tab
    const hash = window.location.hash.replace('#', '') || 'bookings';
    
    function activateTab(name) {
        tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === name));
        panels.forEach(p => p.classList.toggle('active', p.id === `tab-${name}`));
        history.replaceState(null, '', `#${name}`);
    }
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => activateTab(tab.dataset.tab));
    });
    
    // Initial
    const firstTab = document.querySelector(`.profile-tab[data-tab="${hash}"]`) ? hash : (tabs[0]?.dataset.tab || 'bookings');
    activateTab(firstTab);
})();

// ── 9. Movie Detail: Favorite & Watchlist Toggles ─────────────
(function() {
    async function toggleAction(btn, url, key) {
        if (!btn) return;
        const movieId = btn.dataset.movieId;
        try {
            const res  = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({ movie_id: parseInt(movieId) })
            });
            const data = await res.json();
            if (data.success) {
                const added = data.state === 'added';
                if (key === 'fav') {
                    btn.innerHTML = added ? '❤️ Liked' : '🤍 Like';
                    btn.classList.toggle('active', added);
                    showToast(added ? 'Added to Favorites' : 'Removed from Favorites', '', added ? 'success' : 'info', 2500);
                } else {
                    btn.innerHTML = added ? '🔔 In Watchlist' : '🔕 Watchlist';
                    btn.classList.toggle('active', added);
                    showToast(added ? 'Added to Watchlist' : 'Removed from Watchlist', '', added ? 'success' : 'info', 2500);
                }
            }
        } catch { showToast('Error', 'Could not update. Try again.', 'error'); }
    }
    
    const favBtn = document.getElementById('toggle-favorite-btn');
    const wlBtn  = document.getElementById('toggle-watchlist-btn');
    if (favBtn) favBtn.addEventListener('click', () => toggleAction(favBtn, '/api/favorite/toggle/', 'fav'));
    if (wlBtn)  wlBtn.addEventListener('click',  () => toggleAction(wlBtn,  '/api/watchlist/toggle/', 'wl'));
})();

// ── 10. Admin: Revenue Chart ───────────────────────────────────
(function() {
    const canvas = document.getElementById('revenue-chart-canvas');
    if (!canvas) return;
    
    const labels  = JSON.parse(canvas.dataset.labels  || '[]');
    const values  = JSON.parse(canvas.dataset.values  || '[]');
    if (!labels.length) return;
    
    const ctx    = canvas.getContext('2d');
    const W      = canvas.parentElement.offsetWidth || 400;
    const H      = 200;
    canvas.width  = W;
    canvas.height = H;
    
    const max    = Math.max(...values, 1);
    const pad    = { t: 20, r: 20, b: 40, l: 60 };
    const chartW = W - pad.l - pad.r;
    const chartH = H - pad.t - pad.b;
    const step   = chartW / (labels.length - 1);
    
    function toX(i) { return pad.l + i * step; }
    function toY(v) { return pad.t + chartH - (v / max) * chartH; }
    
    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth   = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.t + (i * chartH / 4);
        ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + chartW, y); ctx.stroke();
    }
    
    // Y-axis labels
    ctx.fillStyle = 'rgba(148,163,184,0.8)';
    ctx.font      = '11px Outfit, sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const y = pad.t + (i * chartH / 4);
        const v = Math.round(max * (1 - i / 4));
        ctx.fillText((v / 1000000).toFixed(1) + 'M', pad.l - 8, y + 4);
    }
    
    // Gradient fill
    const grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + chartH);
    grad.addColorStop(0, 'rgba(168,85,247,0.4)');
    grad.addColorStop(1, 'rgba(168,85,247,0.02)');
    
    // Draw area fill
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(values[0]));
    for (let i = 1; i < values.length; i++) {
        const cpX = (toX(i - 1) + toX(i)) / 2;
        ctx.bezierCurveTo(cpX, toY(values[i - 1]), cpX, toY(values[i]), toX(i), toY(values[i]));
    }
    ctx.lineTo(toX(values.length - 1), pad.t + chartH);
    ctx.lineTo(toX(0), pad.t + chartH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
    
    // Draw line
    ctx.beginPath();
    ctx.moveTo(toX(0), toY(values[0]));
    for (let i = 1; i < values.length; i++) {
        const cpX = (toX(i - 1) + toX(i)) / 2;
        ctx.bezierCurveTo(cpX, toY(values[i - 1]), cpX, toY(values[i]), toX(i), toY(values[i]));
    }
    ctx.strokeStyle = 'hsl(271,91%,70%)';
    ctx.lineWidth   = 2.5;
    ctx.stroke();
    
    // Draw dots + labels
    values.forEach((v, i) => {
        // Dot
        ctx.beginPath();
        ctx.arc(toX(i), toY(v), 5, 0, Math.PI * 2);
        ctx.fillStyle   = 'hsl(271,91%,70%)';
        ctx.fill();
        ctx.strokeStyle = 'rgba(15,23,42,0.9)';
        ctx.lineWidth   = 2;
        ctx.stroke();
        
        // X label
        ctx.fillStyle = 'rgba(148,163,184,0.8)';
        ctx.font      = '11px Outfit, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(labels[i], toX(i), H - 10);
        
        // Value tooltip on top
        if (v > 0) {
            ctx.fillStyle = 'rgba(168,85,247,0.9)';
            ctx.font      = '10px Outfit, sans-serif';
            ctx.fillText((v / 1000000).toFixed(1) + 'M', toX(i), toY(v) - 12);
        }
    });
})();

// ── 11. Admin: CSV Upload ──────────────────────────────────────
(function() {
    const form   = document.getElementById('csv-upload-form');
    const status = document.getElementById('upload-status');
    if (!form) return;
    
    form.addEventListener('submit', async e => {
        e.preventDefault();
        const fileInput = document.getElementById('csv-file-input');
        if (!fileInput?.files[0]) return;
        
        const fd = new FormData();
        fd.append('csv_file', fileInput.files[0]);
        
        if (status) { status.style.color = 'var(--text-muted)'; status.textContent = '⏳ Uploading and parsing...'; }
        
        try {
            const res  = await fetch('/api/admin/bulk-upload/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCsrf() } });
            const data = await res.json();
            if (data.success) {
                if (status) { status.style.color = 'var(--success)'; status.textContent = `✅ Imported ${data.count} movies successfully!`; }
                showToast('Import Complete', `${data.count} movies added.`, 'success');
            } else {
                if (status) { status.style.color = 'var(--danger)'; status.textContent = `❌ ${data.error}`; }
            }
        } catch {
            if (status) { status.style.color = 'var(--danger)'; status.textContent = '❌ Upload failed.'; }
        }
    });
})();

// ── 12. Admin: QR Ticket Verify ───────────────────────────────
(function() {
    const form   = document.getElementById('ticket-verify-form');
    const result = document.getElementById('verify-result');
    if (!form) return;
    
    form.addEventListener('submit', async e => {
        e.preventDefault();
        const qr = document.getElementById('qr-scanner-input')?.value.trim();
        if (!qr) return;
        
        try {
            const res  = await fetch('/api/admin/verify-ticket/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({ qr_content: qr })
            });
            const data = await res.json();
            if (result) {
                result.style.display = 'block';
                if (data.success) {
                    result.style.background = 'rgba(16,185,129,0.1)';
                    result.style.borderLeft = '3px solid var(--success)';
                    result.style.padding    = '12px';
                    result.style.borderRadius = '8px';
                    result.innerHTML = `
                        <div style="color:var(--success);font-weight:700;margin-bottom:8px;">✅ Vé Hợp Lệ!</div>
                        <div style="color:var(--text-secondary);font-size:13px;line-height:1.8;">
                            👤 ${data.details.user}<br>
                            🎬 ${data.details.movie}<br>
                            🎫 Ghế: ${data.details.seats}<br>
                            💰 ${parseInt(data.details.price).toLocaleString('vi-VN')} VNĐ
                        </div>
                    `;
                    showToast('Xác Thực Vé Thành Công!', `Khách: ${data.details.user}`, 'success');
                } else {
                    result.style.background = 'rgba(239,68,68,0.1)';
                    result.style.borderLeft = '3px solid var(--danger)';
                    result.style.padding    = '12px';
                    result.style.borderRadius = '8px';
                    result.innerHTML = `<div style="color:var(--danger);font-weight:600;">❌ ${data.error}</div>`;
                    showToast('Vé Không Hợp Lệ', data.error, 'error');
                }
            }
        } catch { showToast('Lỗi', 'Không thể xác thực vé.', 'error'); }
    });
})();

// ── 13. Cancel Booking ─────────────────────────────────────────
(function() {
    document.addEventListener('click', async e => {
        const btn = e.target.closest('.cancel-booking-btn');
        if (!btn) return;
        
        if (!confirm('Bạn có chắc muốn hủy vé này không? Có thể áp dụng hoàn tiền một phần.')) return;
        
        const bookingId = btn.dataset.bookingId;
        btn.disabled    = true;
        btn.textContent = '⏳ Đang Hủy...';
        
        try {
            const res  = await fetch(`/api/booking/cancel/${bookingId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({})
            });
            const data = await res.json();
            if (data.success) {
                showToast('Đã Hủy Vé', `Hoàn tiền: ${parseInt(data.refund_amount || 0).toLocaleString('vi-VN')} VNĐ`, 'info');
                setTimeout(() => location.reload(), 1500);
            } else {
                showToast('Lỗi', data.error, 'error');
                btn.disabled    = false;
                btn.textContent = 'Hủy Vé';
            }
        } catch {
            showToast('Lỗi Kết Nối', 'Vui lòng thử lại.', 'error');
            btn.disabled    = false;
            btn.textContent = 'Hủy Vé';
        }
    });
})();

// ── 14. Star Rating Widget ─────────────────────────────────────
(function() {
    const stars = document.querySelectorAll('.star-rating-btn');
    const input = document.getElementById('rating-hidden-input');
    if (!stars.length) return;
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const val = parseInt(star.dataset.value);
            if (input) input.value = val;
            stars.forEach((s, i) => {
                s.textContent  = i < val ? '★' : '☆';
                s.style.color  = i < val ? 'var(--accent)' : 'var(--text-muted)';
            });
        });
        star.addEventListener('mouseenter', () => {
            const val = parseInt(star.dataset.value);
            stars.forEach((s, i) => s.style.color = i < val ? 'var(--accent)' : 'var(--text-muted)');
        });
        star.addEventListener('mouseleave', () => {
            const val = parseInt(input?.value || 0);
            stars.forEach((s, i) => s.style.color = i < val ? 'var(--accent)' : 'var(--text-muted)');
        });
    });
})();

// ── 15. Loyalty Progress Bar Animation ────────────────────────
(function() {
    const fill   = document.querySelector('.loyalty-progress-fill');
    if (!fill) return;
    const target = fill.dataset.target || '0';
    // Animate after paint
    requestAnimationFrame(() => setTimeout(() => { fill.style.width = target + '%'; }, 100));
})();

// ── 16. Number Count-Up for Metrics ───────────────────────────
(function() {
    const metrics = document.querySelectorAll('[data-countup]');
    if (!metrics.length) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(el => {
            if (!el.isIntersecting) return;
            const target = parseFloat(el.target.dataset.countup);
            const suffix = el.target.dataset.suffix || '';
            const prefix = el.target.dataset.prefix || '';
            const isFloat = !Number.isInteger(target);
            let start = 0;
            const duration = 1200;
            const startTime = performance.now();
            
            function update(now) {
                const elapsed = now - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
                const current = eased * target;
                el.target.textContent = prefix + (isFloat ? current.toFixed(1) : Math.round(current).toLocaleString('vi-VN')) + suffix;
                if (progress < 1) requestAnimationFrame(update);
            }
            requestAnimationFrame(update);
            observer.unobserve(el.target);
        });
    }, { threshold: 0.5 });
    
    metrics.forEach(el => observer.observe(el));
})();

// ── 17. Trailer Modal ──────────────────────────────────────────
(function() {
    const modal    = document.getElementById('trailer-modal');
    if (!modal) return;
    modal.addEventListener('click', e => {
        if (e.target === modal) {
            modal.classList.remove('open');
            // Stop video
            const iframe = modal.querySelector('iframe');
            if (iframe) { const src = iframe.src; iframe.src = ''; iframe.src = src; }
        }
    });
    document.getElementById('open-trailer-btn')?.addEventListener('click', () => modal.classList.add('open'));
    document.getElementById('close-trailer-btn')?.addEventListener('click', () => {
        modal.classList.remove('open');
        const iframe = modal.querySelector('iframe');
        if (iframe) { const src = iframe.src; iframe.src = ''; iframe.src = src; }
    });
})();

// ── 18. Mark Notifications Read ───────────────────────────────
(function() {
    const bell = document.getElementById('nav-notif-bell');
    if (!bell) return;
    bell.addEventListener('click', async () => {
        try {
            await fetch('/api/notifications/read/', { method: 'POST', headers: { 'X-CSRFToken': getCsrf() } });
            const badge = document.getElementById('nav-notif-count');
            if (badge) badge.remove();
        } catch {}
    });
})();

// ── Utility: Get CSRF Token ────────────────────────────────────
function getCsrf() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1]
        || '';
}
