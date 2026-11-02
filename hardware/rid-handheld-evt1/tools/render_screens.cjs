// Optional review rasterization: npm install playwright; playwright install chromium.
const {chromium}=require('playwright');
const path=require('path');
const {pathToFileURL}=require('url');
(async()=>{
  const root=path.resolve(__dirname,'..');
  let browser;
  try {browser=await chromium.launch({headless:true});}
  catch {browser=await chromium.launch({headless:true,channel:'msedge'});}
  try {
    for(const [relative,w,h] of [
      ['interface/radar-demo.svg',240,320],['interface/height-demo.svg',240,320],
      ['mechanical/generated/front-dimensions.svg',1080,760],
      ['mechanical/generated/component-placement.svg',1150,810],
      ['mechanical/generated/stack-dimensions.svg',1100,700]]) {
      const page=await browser.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto(pathToFileURL(path.join(root,relative)).href);
      await page.evaluate(()=>document.fonts.ready);
      await page.screenshot({path:path.join(root,relative.replace('.svg','.png'))});
      if(errors.length)throw new Error(errors.join('\n'));
      await page.close();
    }
  } finally { await browser.close(); }
  console.log('Rendered 5 engineering/UI drawings.');
})().catch(e=>{console.error(e);process.exit(1)});
