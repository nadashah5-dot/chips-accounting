document.addEventListener('DOMContentLoaded', function() {
    // بيع
    document.querySelectorAll('.btn-sell').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = btn.dataset.productId;
            window.location.href = `/inventory/product/${productId}/sell/`;
        });
    });

    // تلف
    document.querySelectorAll('.btn-damage').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = btn.dataset.productId;
            window.location.href = `/inventory/product/${productId}/damage/`;
        });
    });

    // تحويل
    document.querySelectorAll('.btn-transfer').forEach(btn => {
        btn.addEventListener('click', () => {
            const productId = btn.dataset.productId;
            window.location.href = `/inventory/product/${productId}/transfer/`;
        });
    });
});
