# Fees related auth_rule
The next authorization rule extends default auth_map from indy-node ([auth_map](https://github.com/hyperledger/indy-node/blob/master/docs/source/add-node.md))
<table class="tg">
  <tr>
    <th>Transaction type</th>
    <th>Action</th>
    <th>Field</th>
    <th>Previous value</th>
    <th>New value</th>
    <th>Who can</th>
    <th>Description</th>
  </tr>

  <tr>
    <th>SET_FEES</th>
    <th>EDIT</th>
    <th>*</th>
    <th>*</th>
    <th>*</th>
    <th>3 TRUSTEEs</th>
    <th>Setting fees for action/actions</th>
  </tr>