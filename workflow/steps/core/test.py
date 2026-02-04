class VahanPGIGateway(BasePage):
    payment_path_type1 = "vahanpgi/faces/ui/payment.xhtml"
    payment_path_type2 = "eTransPgi/vahanPGIWebService"
    
    
    def __init__(self, page: Page, url, method, data, **kwargs):
        super().__init__(page, **kwargs)
        self.url = url
        self.method = method
        self.data = data
    
    def post_call(self, url, data):
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_selector('.payment-details')
        self.page.evaluate(
            """
            ({ url, method, data }) => {
                const container = document.querySelector('.payment-details');
                if (!container) return;

                container.innerHTML = '';
                const payload = data || {};

                if (method === 'GET') {
                    const params = new URLSearchParams();

                    Object.entries(payload).forEach(([key, value]) => {
                        if (value !== undefined && value !== null) {
                            params.append(
                                key,
                                typeof value === 'object'
                                    ? JSON.stringify(value)
                                    : String(value)
                            );
                        }
                    });
                    const finalUrl = params.toString()
                        ? `${url}?${params.toString()}`
                        : url;

                    window.location.href = finalUrl;
                    return;
                }

                // POST flow
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;

                Object.entries(payload).forEach(([key, value]) => {
                    if (value !== undefined && value !== null) {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value =
                            typeof value === 'object'
                                ? JSON.stringify(value)
                                : String(value);

                        form.appendChild(input);
                    }
                });

                container.appendChild(form);
                form.submit();
            }
            """,
            {
                "url": url,
                "method": self.method,
                "data": self.data
            }
        )
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)
        
    def get_call(self, url, data):
        self.page.goto(url, wait_until="domcontentloaded")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_load_state("load")
        self.page.wait_for_timeout(1000)    
    
    def proceed(self):
        if self.payment_path_type1 in self.url:
            self.get_call(self.url, self.data)
        elif self.payment_path_type2 in self.url:
            self.post_call(self.url, self.data)
        self.wait_for_timeout(2000)
        return self.page.url
    
        