// Artillery processor for custom functions

module.exports = {
  setRandomRegion,
  setRandomRegionAndVpc,
};

const regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'];
const vpcIds = [
  'vpc-0123456789abcdef0',
  'vpc-1234567890abcdef1',
  'vpc-2345678901abcdef2',
  'vpc-3456789012abcdef3'
];

function setRandomRegion(context, events, done) {
  context.vars.region = regions[Math.floor(Math.random() * regions.length)];
  return done();
}

function setRandomRegionAndVpc(context, events, done) {
  context.vars.region = regions[Math.floor(Math.random() * regions.length)];
  context.vars.vpcId = vpcIds[Math.floor(Math.random() * vpcIds.length)];
  return done();
}
