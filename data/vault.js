/* Contour vault: end-to-end encryption for the cloud copy of a person's data.
   Every account has a bundle of secrets, made on the first phone and never sent anywhere readable:
     dk  data key: encrypts the profile, food log, workouts, scans and measurements. A trainer the person
         shares with gets a sealed copy of it.
     hk  health key: encrypts allergies and health conditions. Never shared with anyone.
     pk  a key pair: trainers receive sealed data keys with it. Its public half is published.
   The bundle is stored in the account only wrapped by a key made from the person's Contour passcode,
   so the database, the project owner and any AI see only scrambled bytes.
   On each phone the unwrapped keys are kept in this browser's storage after the first unlock. */
(function(root){
"use strict";
var ITER=600000,subtle=root.crypto&&crypto.subtle,enc=new TextEncoder(),dec=new TextDecoder();
function rnd(n){return crypto.getRandomValues(new Uint8Array(n));}
function b64(u){var s="",i;for(i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s);}
function unb64(s){var b=atob(s),o=new Uint8Array(b.length),i;for(i=0;i<b.length;i++)o[i]=b.charCodeAt(i);return o;}
function kid(){return b64(rnd(9)).replace(/[+/=]/g,"");}

/* ---- this phone's key store ---- */
var dbp=null;
function idb(mode,fn){
  if(!dbp)dbp=new Promise(function(res,rej){var r=indexedDB.open("contourvault",1);r.onupgradeneeded=function(){r.result.createObjectStore("kv");};r.onsuccess=function(){res(r.result);};r.onerror=function(){rej(r.error);};});
  return dbp.then(function(db){return new Promise(function(res,rej){var tx=db.transaction("kv",mode),rq=fn(tx.objectStore("kv"));tx.oncomplete=function(){res(rq?rq.result:undefined);};tx.onerror=tx.onabort=function(){rej(tx.error);};});});
}
function load(uid){return idb("readonly",function(s){return s.get("k:"+uid);});}
function keep(uid,v){return idb("readwrite",function(s){return s.put(v,"k:"+uid);});}
function forget(uid){return idb("readwrite",function(s){return s.delete("k:"+uid);});}

/* ---- keys ---- */
async function kekFrom(pass,salt,iter){
  var base=await subtle.importKey("raw",enc.encode(pass),"PBKDF2",false,["deriveKey"]);
  return subtle.deriveKey({name:"PBKDF2",salt:salt,iterations:iter,hash:"SHA-256"},base,{name:"AES-GCM",length:256},false,["encrypt","decrypt"]);
}
function aes(raw){return subtle.importKey("raw",raw,"AES-GCM",true,["encrypt","decrypt"]);}
async function sealBytes(key,bytes){var iv=rnd(12);return {iv:b64(iv),ct:b64(new Uint8Array(await subtle.encrypt({name:"AES-GCM",iv:iv},key,bytes)))};}
async function openBytes(key,box){return new Uint8Array(await subtle.decrypt({name:"AES-GCM",iv:unb64(box.iv)},key,unb64(box.ct)));}
async function sealJSON(key,obj){return sealBytes(key,enc.encode(JSON.stringify(obj)));}
async function openJSON(key,box){return JSON.parse(dec.decode(await openBytes(key,box)));}

/* The wrapped bundle as stored in the account: {kid, salt, iter, iv, ct}. kid names the current data key. */
async function wrap(kek,salt,iter,dkRaw,hkRaw,pk8,dkid){
  var box=await sealJSON(kek,{dk:b64(dkRaw),hk:b64(hkRaw),pk:b64(pk8)});
  return {kid:dkid,salt:b64(salt),iter:iter,iv:box.iv,ct:box.ct};
}
/* Turns an unwrapped bundle into the keys this phone keeps. */
async function ready(kek,w,inner){
  var dkRaw=unb64(inner.dk),hkRaw=unb64(inner.hk),pk8=unb64(inner.pk);
  var priv=await subtle.importKey("pkcs8",pk8,{name:"ECDH",namedCurve:"P-256"},true,["deriveKey"]);
  var jwk=await subtle.exportKey("jwk",priv);
  return {kek:kek,salt:w.salt,iter:w.iter,kid:w.kid,dk:await aes(dkRaw),hk:await aes(hkRaw),priv:priv,pub:{x:jwk.x,y:jwk.y}};
}
/* First phone ever for this account: make every key. Returns {keys, kw} where kw goes into the account. */
async function create(pass){
  var salt=rnd(16),kek=await kekFrom(pass,salt,ITER),dkRaw=rnd(32),hkRaw=rnd(32);
  var pair=await subtle.generateKey({name:"ECDH",namedCurve:"P-256"},true,["deriveKey"]);
  var pk8=new Uint8Array(await subtle.exportKey("pkcs8",pair.privateKey));
  var w=await wrap(kek,salt,ITER,dkRaw,hkRaw,pk8,kid());
  var keys=await ready(kek,w,{dk:b64(dkRaw),hk:b64(hkRaw),pk:b64(pk8)});
  dkRaw.fill(0);hkRaw.fill(0);pk8.fill(0);
  return {keys:keys,kw:w};
}
/* Another phone, or after the data key changed: open the account's bundle. Throws on a wrong passcode. */
async function unlock(pass,w){
  var kek=await kekFrom(pass,unb64(w.salt),Math.min(Math.max(+w.iter||ITER,100000),2000000));
  return ready(kek,w,await openJSON(kek,w));
}
/* Same passcode, newer bundle (another phone changed the data key): reopen it with the kept passcode key. */
async function refresh(keys,w){return ready(keys.kek,w,await openJSON(keys.kek,w));}
/* Stop sharing: a brand-new data key, so a trainer who had the old one can't open anything new. */
async function rotate(keys){
  var dkRaw=rnd(32),hkRaw=new Uint8Array(await subtle.exportKey("raw",keys.hk)),pk8=new Uint8Array(await subtle.exportKey("pkcs8",keys.priv));
  var w=await wrap(keys.kek,unb64(keys.salt),keys.iter,dkRaw,hkRaw,pk8,kid());
  var next=await ready(keys.kek,w,{dk:b64(dkRaw),hk:b64(hkRaw),pk:b64(pk8)});
  dkRaw.fill(0);hkRaw.fill(0);pk8.fill(0);
  return {keys:next,kw:w};
}
/* New passcode: same keys, wrapped again. */
async function rewrap(keys,pass){
  var salt=rnd(16),kek=await kekFrom(pass,salt,ITER);
  var dkRaw=new Uint8Array(await subtle.exportKey("raw",keys.dk)),hkRaw=new Uint8Array(await subtle.exportKey("raw",keys.hk)),pk8=new Uint8Array(await subtle.exportKey("pkcs8",keys.priv));
  var w=await wrap(kek,salt,ITER,dkRaw,hkRaw,pk8,keys.kid);
  dkRaw.fill(0);hkRaw.fill(0);pk8.fill(0);
  return {keys:await ready(kek,w,await openJSON(kek,w)),kw:w};
}

/* ---- sharing the data key with one trainer ---- */
async function sealTo(pub,raw){
  var their=await subtle.importKey("jwk",{kty:"EC",crv:"P-256",x:pub.x,y:pub.y,ext:true},{name:"ECDH",namedCurve:"P-256"},false,[]);
  var eph=await subtle.generateKey({name:"ECDH",namedCurve:"P-256"},true,["deriveKey"]);
  var k=await subtle.deriveKey({name:"ECDH",public:their},eph.privateKey,{name:"AES-GCM",length:256},false,["encrypt"]);
  var j=await subtle.exportKey("jwk",eph.publicKey),box=await sealBytes(k,raw);
  return {ex:j.x,ey:j.y,iv:box.iv,ct:box.ct};
}
async function shareKey(keys,trainerPub){
  var raw=new Uint8Array(await subtle.exportKey("raw",keys.dk)),box=await sealTo(trainerPub,raw);
  raw.fill(0);box.kid=keys.kid;return box;
}
/* Trainer side: open a member's sealed data key. */
async function openShared(keys,box){
  var epk=await subtle.importKey("jwk",{kty:"EC",crv:"P-256",x:box.ex,y:box.ey,ext:true},{name:"ECDH",namedCurve:"P-256"},false,[]);
  var k=await subtle.deriveKey({name:"ECDH",public:epk},keys.priv,{name:"AES-GCM",length:256},false,["decrypt"]);
  return subtle.importKey("raw",await openBytes(k,box),"AES-GCM",false,["decrypt"]);
}

root.ContourVault={ok:!!(subtle&&root.indexedDB),create:create,unlock:unlock,refresh:refresh,rotate:rotate,rewrap:rewrap,
  sealJSON:sealJSON,openJSON:openJSON,shareKey:shareKey,openShared:openShared,load:load,keep:keep,forget:forget};
})(typeof self!=="undefined"?self:this);
