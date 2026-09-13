window.TFDProfiles={
 all(){try{return JSON.parse(localStorage.getItem('tfd_profiles_v46')||'[]')}catch(e){return[]}},
 active(){const a=this.all(),id=localStorage.getItem('tfd_active_profile_v46');return a.find(x=>x.id===id)||a[0]||null}
};