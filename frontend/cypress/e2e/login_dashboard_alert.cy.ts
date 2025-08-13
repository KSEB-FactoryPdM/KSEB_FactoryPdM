// TODO: Implement e2e login -> dashboard -> alert detail scenario once the app provides these pages

describe('Login to alert detail flow', () => {
  it('navigates from login to dashboard to alert detail', () => {
    // Replace with actual selectors when pages exist
    cy.visit('/login')
    cy.contains('Login').should('exist')
    cy.visit('/monitoring')
    cy.contains('Dashboard').should('exist')
    cy.visit('/alerts/1')
    cy.contains('Alert Detail').should('exist')
  })
})
