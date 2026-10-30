/**
 * SGNIA - Supabase Configuration & Client Module
 * Connects the public portal directly to the Supabase PostgreSQL database via REST API.
 */
window.SGNIA_SUPABASE = {
  url: "https://kjbykrabingylawchnyy.supabase.co",
  anonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqYnlrcmFiaW5neWxhd2Nobnl5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI5MzM0MzQsImV4cCI6MjEwODUwOTQzNH0.T5K5GoszV1CCCIE1Xe0_ml60pVY0WFVcDyKtlE6lI5o",

  /**
   * Helper to perform authenticated GET requests against Supabase REST API
   */
  async request(endpoint, queryParams = {}) {
    const url = new URL(`${this.url}/rest/v1/${endpoint}`);
    for (const [key, value] of Object.entries(queryParams)) {
      url.searchParams.append(key, value);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    try {
      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          apikey: this.anonKey,
          Authorization: `Bearer ${this.anonKey}`,
          Accept: "application/json",
        },
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        throw new Error(`Supabase request to ${endpoint} failed with status ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      clearTimeout(timeout);
      throw err;
    }
  },

  /**
   * Fetch active departments from Supabase
   */
  async getDepartments() {
    return await this.request("departments", {
      active: "eq.true",
      select: "id,name,short_name,code",
      order: "id.asc",
    });
  },

  /**
   * Fetch published notifications from Supabase
   */
  async getPublishedNotifications() {
    return await this.request("notifications", {
      status: "eq.Published",
      select: "id,reference,portal_listing_number,title,category,department,department_code,document_date,official_reference,pdf_url,pdf_path,pdf_sha256,source_url,status",
      order: "document_date.desc,id.desc",
    });
  },
};

