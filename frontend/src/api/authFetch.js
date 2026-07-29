export async function authFetch(url, options = {}) {
  const token = sessionStorage.getItem("td_token");
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
      "Authorization": `Bearer ${token}`,
    },
  });
  if (res.status === 401) {
    window.dispatchEvent(new Event("auth:logout"));
    window.location.replace("/login");
  }
  return res;
}
